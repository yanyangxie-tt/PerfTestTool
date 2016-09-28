# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import copy
import string
import threading

from init_script_env import *
from perf.model.vex_perf_test import VEXPerfTestBase
from perf.parser.manifest import LinearManifestChecker
from utility import time_util


class LinearBitrateResult():
    # 保存某一次bitrate response
    def __init__(self, task, request_time, sequence_number, entertainment_number, ad_number, ad_url_list):
        '''
        Save one bitrate reponse checked result
        @param task: linear task
        @param request_time: bitrate request time(datetime type)
        @param sequence_number: sequence number
        @param entertainment_number: 
        @param ad_number: total ad number
        @param ad_url_list: ad urls
        @param ad_in_first_postion: Boolean, whether ad ts is found in the first position in manifest
        '''
        
        self.task = task
        self.request_time = request_time
        self.ad_number = ad_number
        self.ad_url_list = ad_url_list
        self.sequence_number = sequence_number
        self.entertainment_number = entertainment_number
        self.exist_ad = True if self.ad_number > 0 else False
    
    def __repr__(self):
        return '%s[%s]:sequence_number:%s, entertainment number:%-2s, ad number:%-2s' \
            % (self.task.get_client_ip(), self.request_time, self.sequence_number, self.entertainment_number, self.ad_number)

class LinearBitrateResultTrace():
    '''保存一个bitrate的全部运行状态'''
    def __init__(self, task, ad_insertion_frequency='200/20', content_segment_time=2, sequence_increase_request_number=2):
        # sequence_increase_gap: senquence number 增长的最大请求数量。对t6来说，2秒请求一次。那么2次请求sequence number就必须增长了
        
        self.lock = threading.RLock()
        self.task = task
        self.bitrate_url = task.get_bitrate_url()
        self.bitrate_result_list = []
        self.ad_insertion_frequency = ad_insertion_frequency
        self.content_segment_time = content_segment_time
        self.entertainment_ts_gap = int(ad_insertion_frequency.split('/')[0]) * content_segment_time
        self.max_ad_number_in_ad_interval = int(ad_insertion_frequency.split('/')[1])
        self.sequence_increase_request_number = sequence_increase_request_number
        
        self.error_list = []
        
    def add_bitrate_result(self, result):
        if not isinstance(result, LinearBitrateResult):
            return
        
        with self.lock:
            self.bitrate_result_list.append(result)
    
    def check(self):
        if len(self.bitrate_result_list) == 0:
            return

        # check的时候，bitrate response仍然在不停的往其中添加。因此需要锁定这个bitrate_result_trace这个list。
        # 也就是说，当检查的时候，把bitrate response给复制出来，然后让bitrate_result_trace变成[]. 如果有没有被check的，则在插回到这个list的前边
        with self.lock:
            bitrate_result_list = copy.copy(self.bitrate_result_list)
            self.bitrate_result_list = []
        
        # 首先分组bitrate url list.(cdvr的无需分组。没遇见endlist就不检查)
        bitrate_group_list = self.group_result(bitrate_result_list)
        
        # 最后一个分组，不确定是不是完整的，因此，不check。直接把它加回去到trace 列表中
        latest_bitrate_group = bitrate_group_list.pop(-1)
        with self.lock:
            self.bitrate_result_list = latest_bitrate_group + self.bitrate_result_list
        
        # 接下来，针对每个bitrate 分组，进行分析
        for bitrate_group in bitrate_group_list:
            self.analysis_bitrate_group(bitrate_group)
    
    def group_result(self, bitrate_result_list):
        # 分组bitrate url list. 使得每组bitrate_results都是由正常的没有ad的manifest开始。到出现ad的manifest.
        # 分组的依据是前一个还是ad，后一个没有ad。说明一个ad周期结束了
        if len(bitrate_result_list) == 0:
            return []
        
        total_groups = []
        groups = []
        
        for i, bitrate_result in enumerate(bitrate_result_list):
            if i == 0:
                groups.append(bitrate_result)
            elif bitrate_result_list[i - 1].exist_ad is True and bitrate_result.exist_ad is not True:
                # 前一个manifest包含ad，现在的manifest不包含ad,则是一个ad insertion周期结束
                total_groups.append(groups)
                groups = []
                groups.append(bitrate_result)
            else:
                groups.append(bitrate_result)
        
        if len(groups) > 0:
            total_groups.append(groups)
        
        return total_groups

    # 如何加单元测试，测试这个方法？
    def analysis_bitrate_group(self, bitrate_result_list):
        ad_url_set = set([])
        for i, bitrate_result in enumerate(bitrate_result_list):
            if i > self.sequence_increase_request_number:
                # 两个bitrate response间隔sequence_increase_request_number，sequence应该增加，否则记录错误
                pre_bitrate_result = bitrate_result_list[i - self.sequence_increase_request_number]
                if bitrate_result.sequence_number <= pre_bitrate_result.sequence_number:
                    self.error_list.append('Sequence number is not increased. %s:%s, %s:%s' \
                            % (pre_bitrate_result.request_time, pre_bitrate_result.sequence_number, bitrate_result.request_time, bitrate_result.sequence_number,))
                
                if bitrate_result.ad_number > 0:
                    ad_url_set.union(set(bitrate_result.ad_url_list))
        
        if len(ad_url_set) != self.max_ad_number_in_ad_interval:
            # 如果ad的数量少于期待值, 记录错误
            self.error_list.append('AD number is not as expected. Time window: %s~%s. ad number:%s, expected ad number: %s' \
                    %(bitrate_result_list[0].request_time, bitrate_result_list[-1].request_time ,len(ad_url_set), self.max_ad_number_in_ad_interval))

class LinearPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param current_process_index: used to generate current concurrent request number , should less than total process number
        @param log_file: log file absolute path
        '''
        super(LinearPerfTest, self).__init__(config_file, current_process_index=current_process_index, **kwargs)
    
    def set_component_private_default_value(self):
        self._set_attr('client_response_asset_tag', 'test')
        self._set_attr('test_type_options', ['LINEAR_T6', 'LINEAR_TVE'])
        self._set_attr('index_url_format', 'http://mm.linear.%s.comcast.net/%s/index.m3u8?StreamType=%s&ProviderId=%s&PartnerId=private:cox&dtz=2014-11-04T11:09:26-05:00&AssetId=abcd1234567890123456&DeviceId=1')
        self._set_attr('warm_up_time_gap', 60)  # in warm up stage, time gap in each requests bundle
        self._set_attr('test_use_iframe', False, True)
        self._set_attr('test_require_sap', False)
        self._set_attr('fake_file_dir', os.path.dirname(os.path.realpath(__file__)))
        self._set_attr('test_bitrate_call_interval', 2)
        self._set_attr('test_client_bitrate_request_frequency', 2)
        
        self._set_attr('record_client_number', True, True)
        self.client_number_dict = {}
        self.check_client_ip_dict = {}
    
    def set_component_private_environment(self):
        self.set_checked_client_number()
    
    def set_checked_client_number(self):
        checked_client_number = int(self.current_processs_concurrent_request_number * self.client_response_check_percent)
        self.checked_client_number = 1 if checked_client_number < 1 else checked_client_number
    
    def generate_index_url(self):
        content_name = self._get_random_content()
        return self.index_url_format % (content_name, content_name, self.test_case_type, content_name)
    
    def dispatch_task_with_max_request(self):
        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=2)
        self.dispatch_task_sched.add_interval_job(self._supply_request_to_max_client, start_date=start_date, seconds=self.test_client_bitrate_request_frequency)
    
    def _supply_request_to_max_client(self):
        try:
            with self.index_lock:
                if len(self.client_number_dict) < self.current_processs_concurrent_request_number:
                    self.logger.debug('Supply: running test client number is %s, less than the expected %s, supply it.' % (len(self.client_number_dict), self.current_processs_concurrent_request_number))
                    gap = self.current_processs_concurrent_request_number - len(self.client_number_dict)
                    for i in range(0, gap):
                        task = self.task_queue.get(True, timeout=10)
                        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=1)
                        task.set_start_date(start_date)
                        self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
                        self.logger.debug('Supply: add %s task to test' % (i + 1))
        except Exception, e:
            self.logger.fatal(e)
            exit(1)
    
    def do_index_other_step(self, task):
        # To linear and cdvr, record its client ip to do check and supply with max client
        self.client_number_dict[task.get_client_ip()] = task
    
    def schedule_bitrate(self, task, bitrate_url_list):
        for i, bitrate_url in enumerate(bitrate_url_list):
            b_task = task.clone()
            delta_milliseconds = self.test_bitrate_serial_time * (i + 1) if self.test_bitrate_serial else self.test_bitrate_serial_time
            start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_milliseconds=delta_milliseconds)
            b_task.set_bitrate_url(bitrate_url)
            b_task.set_start_date(start_date)
            self.logger.debug('Schedule bitrate interval request at %s, interval is %s. task:%s' % (start_date, self.test_client_bitrate_request_frequency, b_task))
            self.task_consumer_sched.add_interval_job(self.do_bitrate, start_date=start_date, seconds=self.test_client_bitrate_request_frequency, args=(b_task,))
    
    def do_bitrate_other_step(self, task, response_text):
        checker = None
        if not self._has_attr('client_response_check_when_running') is True and not self._has_attr('send_psn_message') is True:
            return
        
        if self._has_attr('client_response_check_when_running'):
            with self.bitrate_lock:
                client_ip = task.get_client_ip()
                if len(self.check_client_ip_dict) < self.checked_client_number and not self.check_client_ip_dict.has_key(client_ip):
                    self.check_client_ip_dict[client_ip] = LinearBitrateResultTrace(task, self.client_response_ad_frequecy, self.client_response_content_segment_time)
                    self.logger.info('Add client %s into checked list. Current check client is %s, max is %s' % (client_ip, len(self.check_client_ip_dict), self.checked_client_number))
            
            if self.check_client_ip_dict.has_key(client_ip) and task.get_bitrate_url() == self.check_client_ip_dict[client_ip].bitrate_url:
                checker = LinearManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag=self.client_response_media_tag, asset_id_tag=self.client_response_asset_tag)
                
                ad_url_list = checker.ad_url_list
                ad_number = checker.ad_ts_number
                sequence_number = checker.sequence_number
                entertainment_number = checker.entertainment_ts_number
                
                # Same client, one index with multiple bitrate, only record one bitrate response trace
                request_time = time_util.get_local_now()
                bitrate_result = LinearBitrateResult(task, request_time, sequence_number, entertainment_number, ad_number, ad_url_list)
                
                with self.bitrate_lock:
                    self.check_client_ip_dict[client_ip].add_bitrate_result(bitrate_result)
                self.logger.info('Store bitrate response. %s' % (bitrate_result))
        
        if self._has_attr('send_psn_message') is True:
            if checker is None:
                checker = LinearManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag=self.client_response_media_tag, asset_id_tag=self.client_response_asset_tag)
            
            psn_gap_list = [1 + int(self.client_response_content_segment_time * self.client_response_ad_ts_number * float(i)) for i in self.psn_message_sender_position]
            if self._has_attr('psn_send') is True:
                self.send_psn(task, checker.psn_tracking_position_id_dict, psn_gap_list)
    
    def analysis_traced_bitrate_response(self):
        self.logger.info('Analysis traced bitrate reponse. Checked client number is %s' % (self.check_client_ip_dict))
        for client_ip, bitrate_result_trace in self.check_client_ip_dict.items():
            self.do_bitrate_result_trace_check(client_ip, bitrate_result_trace)
    
    def do_bitrate_result_trace_check(self, client_ip, bitrate_result_trace):
        print 'bitrate_result_trace.bitrate_result_list size:%s' %(len(bitrate_result_trace.bitrate_result_list)) 
        bitrate_result_trace.check()
        
        if len(bitrate_result_trace.error_list) != 0:
            bitrate_result_trace.error_list.insert(0, client_ip)
            error_contents = string.join(bitrate_result_trace.error_list, '\n')
            
            self.error_record_queue.put(error_contents)
            bitrate_result_trace.error_list = []
    
    def _generate_warm_up_list(self):
        total_number = self.current_processs_concurrent_request_number
        warm_up_period_minute = self.test_case_warmup_period_minute
        
        number, remainder_number = divmod(total_number, warm_up_period_minute) if total_number > warm_up_period_minute else (1, 0)
        
        warm_up_minute_list = []
        for i in range(0, warm_up_period_minute):
            warm_up_minute_list.append(number)
        
        if remainder_number is not 0:
            warm_up_minute_list = warm_up_minute_list[:-1] + [remainder_number, ]
        
        return warm_up_minute_list

if __name__ == '__main__':
    current_process_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    pert_test = LinearPerfTest(config_file, current_process_index, golden_config_file=golden_config_file)
    pert_test.run()
