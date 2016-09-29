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
    '''Save one parsed bitrate response info'''
    
    def __init__(self, task, request_time, sequence_number, entertainment_number, ad_number, ad_url_list):
        '''
        @param task: linear request task
        @param request_time: bitrate request time(datetime)
        @param sequence_number: sequence number
        @param entertainment_number: total entertainment ts number
        @param ad_number: total ad ts number
        @param ad_url_list: ad url list
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
    '''Traced one client bitrate requests and response, and then check the traced response'''
    def __init__(self, task, ad_insertion_frequency='200/20', content_segment_time=2, sequence_increase_request_number=2):
        '''
        @param task: linear request task
        @param ad_insertion_frequency: same as the ad_insertion_frequency in mock origin
        @param content_segment_time: time of one ts
        @param sequence_increase_request_number: how often that segment number must be increased.
                    Take t6linear for example, vex will do manifest expansion every 2 second and client call vex every second, 
                    so at least two request will make segment number increase by 1.
        '''
        
        self.lock = threading.RLock()
        self.task = task
        self.bitrate_url = task.get_bitrate_url()
        self.bitrate_result_list = []
        self.ad_insertion_frequency = ad_insertion_frequency
        self.content_segment_time = content_segment_time
        self.ad_number_in_complete_cycle = int(ad_insertion_frequency.split('/')[1])
        self.entertainment_number_in_complete_cycle = int(ad_insertion_frequency.split('/')[0])
        self.sequence_increase_request_number = sequence_increase_request_number
        
        self.error_list = []
        
    def add_bitrate_result(self, result):
        # store one bitrate result of one client
        if not isinstance(result, LinearBitrateResult):
            return
        
        with self.lock:
            self.bitrate_result_list.append(result)
    
    def check(self, logger=None):
        if logger is not None:
            self.logger = logger
        
        if len(self.bitrate_result_list) == 0:
            return

        # while checking, test client is also running, and bitrate result is still be inserted into the traced list
        # so need to copy the current static traced datas and do data analysis using those static traced datas
        with self.lock:
            bitrate_result_list = copy.copy(self.bitrate_result_list)
            self.bitrate_result_list = []
        
        # 1st, separate bitrate url list to multiple data segment
        self.log_debug('Bitrate list in checked list:\n%s' %(bitrate_result_list))
        bitrate_group_list, has_ad_in_total = self.group_result(bitrate_result_list)
        self.log_debug('Checked list has ad:%s, Grouped result list is:\n%s' %(has_ad_in_total, bitrate_group_list))
        
        # 2st, if separated list(group list) has only one element, then it maybe has no ad. So need check whether its request number is larger than expected
        # if no ad, then record the error
        if len(bitrate_group_list) == 1 and has_ad_in_total is False:
            if len(bitrate_group_list[0]) > self.entertainment_number_in_complete_cycle:
                message = 'No ad found in one ad-insertion cycle. Entertainment number is %s, larger than %s. Time window: %s~%s.' \
                    %(len(bitrate_group_list[0]), self.entertainment_number_in_complete_cycle, bitrate_group_list[0][0].request_time, bitrate_result_list[-1].request_time, )
                self.record_error(message)
                return
        
        # to the latest element, not sure whether it is one completely ad-insertion cycle, so not check it but re-add it into system bitrate result traced list
        latest_bitrate_group = bitrate_group_list.pop(-1)
        with self.lock:
            self.bitrate_result_list = latest_bitrate_group + self.bitrate_result_list
        
        self.log_debug('Grouped result list(Removed latest) is:\n%s' %(bitrate_group_list))
        for bitrate_group in bitrate_group_list:
            self.analysis_bitrate_group(bitrate_group)
    
    def group_result(self, bitrate_result_list):
        '''
        Separate traced bitrate result list to multiple segments which is one completely ad-insertion cycle, such as 300/30 
        Separate rule is that one manifest has not ad, but previous one has ad. then here is the traced list separator
        Each data segment must start with (manifest without ad), and end with (manifest with ad)
        For example. 0 means one manifest without ad, 1 means one manifest with ad.
        [0,1,1,1,1,0,0,0,1,1,1,0,0,0,1,1,1,0,0]
            --> [[0, 1, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0,0]]
        
        [1,1,0,0,0,1,1,1,0,0,0,1,1,1,0,0]
            --> [[1, 1], [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0,0]]
        '''
        if len(bitrate_result_list) == 0:
            return []
        
        has_ad_in_total = False
        total_groups = []
        groups = []
        
        for i, bitrate_result in enumerate(bitrate_result_list):
            if i == 0:
                groups.append(bitrate_result)
            elif bitrate_result_list[i - 1].exist_ad is True and bitrate_result.exist_ad is not True:
                # one manifest has not ad, but previous has ad
                total_groups.append(groups)
                groups = []
                groups.append(bitrate_result)
                has_ad_in_total = True
            else:
                groups.append(bitrate_result)
        
        if len(groups) > 0:
            total_groups.append(groups)
        
        return total_groups, has_ad_in_total

    def analysis_bitrate_group(self, bitrate_result_list):
        if len(bitrate_result_list) == 0:
            return
        
        # if first element in bitrate_result_list is ad, then it is one completely ad-insertion cycle, ignore it
        if bitrate_result_list[0].exist_ad is True:
            return
        
        ad_url_set = set([])
        entertainment_request_size = 0
        for i, bitrate_result in enumerate(bitrate_result_list):
            if i > self.sequence_increase_request_number:
                pre_bitrate_result = bitrate_result_list[i - self.sequence_increase_request_number]
                if bitrate_result.sequence_number <= pre_bitrate_result.sequence_number:
                    message = 'Sequence number is not increased. %s:%s, %s:%s' \
                            % (pre_bitrate_result.request_time, pre_bitrate_result.sequence_number, bitrate_result.request_time, bitrate_result.sequence_number,)
                    self.record_error(message)
                
            if bitrate_result.ad_number > 0:
                ad_url_set = ad_url_set.union(set(bitrate_result.ad_url_list))
            else:
                entertainment_request_size += 1
        
        if entertainment_request_size > self.entertainment_number_in_complete_cycle:
            message = 'No ad found in one ad-insertion cycle. Entertainment number is %s, larger than %s. Time window: %s~%s.' \
                    %(entertainment_request_size, self.entertainment_number_in_complete_cycle, bitrate_result_list[0].request_time, bitrate_result_list[-1].request_time, )
            self.record_error(message)
        
        if len(ad_url_set) != self.ad_number_in_complete_cycle:
            message = 'AD number is not as expected. Ad number:%s, expected ad number: %s. Time window: %s~%s. ' \
                    %(len(ad_url_set), self.ad_number_in_complete_cycle, bitrate_result_list[0].request_time, bitrate_result_list[-1].request_time,)
            self.record_error(message)
    
    def log_debug(self, message):
        if self.logger: self.logger.debug('%s:%s.' %(self.task.get_client_ip(), message))
    
    def record_error(self, message):
        self.error_list.append(message)
        if self.logger: self.logger.error('%s:%s.' %(self.task.get_client_ip(), message))
    
class LinearPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param current_process_index: used to generate current concurrent request number , should less than total process number
        @param log_file: log file absolute path
        '''
        super(LinearPerfTest, self).__init__(config_file, current_process_index=current_process_index, **kwargs)
    
    def set_component_private_default_value(self):
        self.export_concurrent_number = False
        
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
                self.logger.debug('Store bitrate response. %s' % (bitrate_result))
        
        if self._has_attr('send_psn_message') is True:
            if checker is None:
                checker = LinearManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag=self.client_response_media_tag, asset_id_tag=self.client_response_asset_tag)
            
            psn_gap_list = [1 + int(self.client_response_content_segment_time * self.client_response_ad_ts_number * float(i)) for i in self.psn_message_sender_position]
            if self._has_attr('psn_send') is True:
                self.send_psn(task, checker.psn_tracking_position_id_dict, psn_gap_list)
    
    def analysis_traced_bitrate_response(self):
        self.logger.debug('Analysis traced bitrate reponse. Checked client number is %s' % (self.check_client_ip_dict))
        for client_ip, bitrate_result_trace in self.check_client_ip_dict.items():
            self.do_bitrate_result_trace_check(client_ip, bitrate_result_trace)
    
    def do_bitrate_result_trace_check(self, client_ip, bitrate_result_trace):
        bitrate_result_trace.check(self.logger)
        
        if len(bitrate_result_trace.error_list) != 0:
            error_contents = client_ip + '::'
            error_contents += string.join(bitrate_result_trace.error_list, '||')
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
