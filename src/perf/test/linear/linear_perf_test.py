# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from init_script_env import *
from perf.model.vex_perf_test import VEXPerfTestBase
from utility import time_util
import datetime

class LinearBitrateResult():
    # 保存某一次bitrate response
    def __init__(self, time_long, bitrate_response):
        self.time_long = time_long
        self.bitrate_response = bitrate_response
        self.parse_bitrate_response(bitrate_response)
    
    def parse_bitrate_response(self, bitrate_response):
        pass
    
    def __repr__(self):
        return self.time_long

class LinearBitrateResultTrace():
    '''保存一个bitrate的全部运行状态'''
    def __init__(self, task):
        self.task = task
        self.bitrate_url = task.get_bitrate_url()
        self.bitrate_result_list = []
        
    def add_bitrate_result(self, result):
        if not isinstance(result, LinearBitrateResult):
            return
        
        self.bitrate_result_list.append(result)

class LinearPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param current_process_index: used to generate current concurrent request number , should less than total process number
        @param log_file: log file absolute path
        '''
        super(LinearPerfTest, self).__init__(config_file, current_process_index=current_process_index, **kwargs)
    
    def set_component_private_default_value(self):
        self._set_attr('test_type_options', ['LINEAR_T6','LINEAR_TVE'])
        self._set_attr('index_url_format', 'http://mm.linear.%s.comcast.net/%s/index.m3u8?StreamType=%s&ProviderId=%s&PartnerId=private:cox&dtz=2014-11-04T11:09:26-05:00&AssetId=abcd1234567890123456&DeviceId=1')
        self._set_attr('warm_up_time_gap', 60) # in warm up stage, time gap in each requests bundle
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
                    self.logger.debug('Supply: running test client number is %s, less than the expected %s, supply it.' %(len(self.client_number_dict), self.current_processs_concurrent_request_number))
                    gap = self.current_processs_concurrent_request_number - len(self.client_number_dict)
                    for i in range(0, gap):
                        task = self.task_queue.get(True, timeout=10)
                        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=1)
                        task.set_start_date(start_date)
                        self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
                        self.logger.debug('Supply: add %s task to test' %(i + 1))
        except Exception, e:
            exit(1)
    
    def do_index_other_step(self, task):
        # To linear and cdvr, record its client ip to do check and supply with max client
        self.client_number_dict[task.get_client_ip()]=task
    
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
        if self._has_attr('send_psn_message') is False and self._has_attr('client_response_check_when_running') is False:
            return
        
        if self._has_attr('client_response_check_when_running'):
            with self.bitrate_lock:
                client_ip = task.get_client_ip()
                if len(self.check_client_ip_dict) < self.checked_client_number and not self.check_client_ip_dict.has_key(client_ip):
                    self.check_client_ip_dict[client_ip]=LinearBitrateResultTrace(task)
                
            if self.check_client_ip_dict.has_key(client_ip) and task.get_bitrate_url() == self.check_client_ip_dict[client_ip].bitrate_url:
                # 同一个index，访问多个bitrate，只存储一个bitrate的状态
                time_long = time_util.datetime_2_long(time_util.get_local_now())
                self.logger.info('Store bitrate response. time:%s, bitrate url: %s' %(time_long, task.get_bitrate_url()))
                bitrate_result = LinearBitrateResult(time_long, response_text)
                self.check_client_ip_dict[client_ip].add_bitrate_result(bitrate_result)
        
        if self._has_attr('send_psn_message') is True:
            # 发送psn
            #linear的client_response_ad_mid_roll_ts_number应该是每个ad的秒数，需要配置下。
            #t6linear ad的number是15个ts, self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number= 2*15
            #tvelinear ad的number是5个ts, self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number= 6*5
            #psn_gap_list = [1 + int(self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number * float(i)) for i in self.psn_message_sender_position]
            #if self._has_attr('psn_send') is True:
            #    self.send_psn(task, checker.psn_tracking_position_id_dict, psn_gap_list)
            #elif self._has_attr('psn_fake_send') is True:
            #    self.send_psn(task, self.psn_fake_tracking_position_id_dict, psn_gap_list)
            #
            #if self._has_attr('psn_endall_send') is True:
            #    self.send_endall_psn(task)
            pass
    
    def check_response(self, task, manifest_checker):
        # linear的check response需要定时触发
        # cdvr的check response是在遇到endlist tag的时候触发。以及定时触发(为了防止一直没有endlist tag)
        
        pass
    
    def _generate_warm_up_list(self):
        total_number = self.current_processs_concurrent_request_number
        warm_up_period_minute = self.test_case_warmup_period_minute
        
        number, remainder_number = divmod(total_number, warm_up_period_minute) if total_number > warm_up_period_minute else (1,0)
        
        warm_up_minute_list = []
        for i in range(0, warm_up_period_minute):
            warm_up_minute_list.append(number)
        
        if remainder_number is not 0:
            warm_up_minute_list = warm_up_minute_list[:-1] + [remainder_number,]
        
        return warm_up_minute_list

if __name__ == '__main__':
    current_process_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    pert_test = LinearPerfTest(config_file, current_process_index, golden_config_file=golden_config_file)
    pert_test.run()
