# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from init_script_env import *
from perf.model.vex_perf_test import VEXPerfTestBase
from perf.parser.manifest import LinearManifestChecker
from utility import time_util

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
        
        self._set_attr('store_client_index_info', True, True)
        self.client_index_dict = {}
    
    def generate_index_url(self):
        content_name = self._get_random_content()
        return self.index_url_format % (content_name, content_name, self.test_case_type, content_name)
    
    def dispatch_task_with_max_request(self):
        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=2)
        self.dispatch_task_sched.add_interval_job(self._supply_request_to_max_client, start_date=start_date, seconds=self.test_client_bitrate_request_frequency)
    
    def _supply_request_to_max_client(self):
        while(True):
            if len(self.client_index_dict) < self.current_processs_concurrent_request_number:
                self.logger.debug('Supply: running test client number is %s, less than the expected %s, supply it.' %(len(self.client_index_dict), self.current_processs_concurrent_request_number))
                task = self.task_queue.get(True, timeout=10)
                start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=1)
                task.set_start_date(start_date)
                self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
            else:
                break
    
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
        # check or send psn
        if self._has_attr('send_psn_message') is False and self._has_attr('client_response_check_when_running') is False:
            return
        
        # check
        
        # linear要好好想想，bitrate请求出错了。怎么处理？持续retry？还是重发一个其他的index?
        # linear的重试次数要加大，至少要10次。然后bitrate failed重试10次
        # 弄一个dict。key是client ip。然后查dict的len, 如果比期望的最大并发小，那么在distribute task的定期检查中，发index request补全
        # 这样，当index失败了的话，不会往这个池子里加任务。distribute task会补全压力。
        # 当bitrate失败的话，从这个dict中移除client ip.这样也会补全压力
        # 对于cdvr。也可以这么做。当遇到endlist tag的时候，从这个dict中移除client ip
        # 按照上述的设计。task_generater就应该维持一定的量。和vod的task_generater是一样的。只不过由task distribute来控制是不是读取task queue
        # linear的result验证怎么办？
        
        '''
        #
        self.logger.debug('Bitrate response for task[%s]:\n%s' % (task, response_text,))
        checker = LinearManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_')
        
        if self._has_attr('client_response_check_when_running') is True:
            self.check_response(task, checker)
        
        if self._has_attr('send_psn_message') is True:
            linear的client_response_ad_mid_roll_ts_number应该是每个ad的秒数，需要配置下。
            t6linear ad的number是15个ts, self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number= 2*15
            tvelinear ad的number是5个ts, self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number= 6*5
            psn_gap_list = [1 + int(self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number * float(i)) for i in self.psn_message_sender_position]
            if self._has_attr('psn_send') is True:
                self.send_psn(task, checker.psn_tracking_position_id_dict, psn_gap_list)
            elif self._has_attr('psn_fake_send') is True:
                self.send_psn(task, self.psn_fake_tracking_position_id_dict, psn_gap_list)
            
            if self._has_attr('psn_endall_send') is True:
                self.send_endall_psn(task)
        '''
    
    def check_response(self, task, manifest_checker):
        pass
        '''
        with self.bitrate_lock:
            if self.bitrate_counter.total_count % self.check_percent_factor != 0:
                return
        
        self.logger.debug('Check bitrate client response. task: %s' %(task))
        error_message = manifest_checker.check(self.client_response_media_sequence, self.client_response_content_segment_number,
                self.client_response_endlist_tag, self.client_response_drm_tag, self.client_response_ad_mid_roll_position, self.client_response_ad_pre_roll_ts_number,
                self.client_response_ad_mid_roll_ts_number, self.client_response_ad_post_roll_ts_number,)
        if error_message is not None and error_message != '':
            if self._has_attr('client_response_error_dump') is True:
                self.logger.error('%s, Manifest:%s' % (error_message, manifest_checker.manifest))
            else:
                self.logger.error('%s' % (error_message))
            
            self.error_record_queue.put('%-17s: %s' % (task.get_client_ip(), error_message), False, 2)
            self._increment_counter(self.bitrate_counter, self.bitrate_lock, is_error_response=True)
        '''
    
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
