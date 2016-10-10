# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import hashlib
import random
import string

from init_script_env import *
from perf.model.vex_perf_test import VEXPerfTestBase
from perf.parser.manifest import CdvrManifestChecker
from perf.test.cdvr.cdvr_trace import CdvrBitrateResultTrace, CdvrBitrateResult
from utility import time_util

test_type_options = ['CDVR_T6', ]
index_url_format = 'http://mm.cdvr.comcast.net/%s/index.m3u8?RecordingId=%s&StreamType=%s&ProviderId=1234567&AssetId=king1234567890123456&DeviceId=1'
    
class CdvrPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param current_process_index: used to generate current concurrent request number , should less than total process number
        @param log_file: log file absolute path
        '''
        super(CdvrPerfTest, self).__init__(config_file, current_process_index=current_process_index, **kwargs)
    
    def set_component_private_default_value(self):
        self._set_attr('export_concurrent_number', False, True)
        self._set_attr('client_response_asset_tag', 'cdvr')
        self._set_attr('test_type_options', test_type_options)
        self._set_attr('index_url_format', index_url_format)
        self._set_attr('warm_up_time_gap', 60)  # in warm up stage, time gap in each requests bundle
        self._set_attr('test_use_iframe', False)
        self._set_attr('test_require_sap', False)
        self._set_attr('fake_file_dir', os.path.dirname(os.path.realpath(__file__)))
        self._set_attr('test_bitrate_call_interval', 2)
        self._set_attr('test_client_bitrate_request_frequency', 2)
        self._set_attr('test_case_fixed_recording', False)
        
        # Indicate how many client is alive in performance test, key is client ip, value is task
        self.alived_client_recorder_dict = {}
        
        # Record bitrate response for checked clients. Key is client ip, value is bitrate response trace
        self.check_client_ip_dict = {}
        
        # Record the client bitrate request jobs. Key is (bitrate_url+client_ip), value is apscheduler job
        self.job_recorder = {}
    
    def set_component_private_environment(self):
        self.set_checked_client_number()
    
    def set_checked_client_number(self):
        if self.test_case_fixed_recording is True:
            # To performance test of fixed recording, checked client number is based on concurrent request number.
            # While meeting delta dump time window, the checked client info will be removed from checked dict
            checked_client_number = int(self.current_processs_concurrent_request_number * self.client_response_check_percent * self.test_case_counter_dump_interval)
        else:
            checked_client_number = int(self.current_processs_concurrent_request_number * self.client_response_check_percent)
        self.checked_client_number = 1 if checked_client_number < 1 else checked_client_number
    
    def generate_index_url(self):
        # To cdvr, different client watchs a different recording
        content_name = self._get_random_content() + '_' + str(random.randint(0, 1000 * 1000))
        return self.index_url_format % (content_name, content_name, self.test_case_type)
    
    def dispatch_task_with_max_request(self):
        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=2)
        self.dispatch_task_sched.add_interval_job(self._supply_request_to_max_client, start_date=start_date, seconds=1)
    
    def _supply_request_to_max_client(self):
        # while recording is to end, will never call the cdvr recording any more. Need supply a new recording to meet the max client number.
        try:
            with self.index_lock:
                if len(self.alived_client_recorder_dict) < self.current_processs_concurrent_request_number:
                    self.logger.debug('Supply: running test client number is %s, less than the expected %s, supply new recordings.' % (len(self.alived_client_recorder_dict), self.current_processs_concurrent_request_number))
                    gap = self.current_processs_concurrent_request_number - len(self.alived_client_recorder_dict)
                    for i in range(0, gap):
                        task = self.task_queue.get(True, timeout=10)
                        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_milliseconds=100)
                        task.set_start_date(start_date)
                        self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
                        self.logger.debug('Supply: add %s task to test. task:%s' % (i + 1, task))
        except Exception, e:
            self.logger.fatal(e)
            exit(1)
    
    def do_index_subsequent_step(self, task):
        # The alived_client_recorder_dict is to indicate how many client is alive in performance test, so need to record succeed task
        self.alived_client_recorder_dict[task.get_client_ip()] = task
        
        client_ip = task.get_client_ip()
        if len(self.check_client_ip_dict) < self.checked_client_number and not self.check_client_ip_dict.has_key(client_ip):
            self.check_client_ip_dict[client_ip] = None
            self.logger.debug('Add client %s into check list. Current checked client is %s, max is %s' % (client_ip, len(self.check_client_ip_dict), self.checked_client_number))
    
    def schedule_bitrate(self, task, bitrate_url_list):
        for i, bitrate_url in enumerate(bitrate_url_list):
            b_task = task.clone()
            delta_milliseconds = self.test_bitrate_serial_time * (i + 1) if self.test_bitrate_serial else self.test_bitrate_serial_time
            start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_milliseconds=delta_milliseconds)
            b_task.set_bitrate_url(bitrate_url)
            b_task.set_start_date(start_date)
            self.logger.debug('Schedule bitrate interval request at %s, interval is %s. task:%s' % (start_date, self.test_client_bitrate_request_frequency, b_task))
            
            job_name = self._generate_job_name(b_task)
            job = self.task_consumer_sched.add_interval_job(self.do_bitrate, start_date=start_date, seconds=self.test_client_bitrate_request_frequency, args=(b_task,), name=job_name)
            self.job_recorder[job_name] = job
            self.logger.debug('Add bitrate interval job %s, %s' %(job_name, job))
    
    def do_bitrate_subsequent_step(self, task, response_text):
        is_fixed_recording = True if self.test_case_fixed_recording is True or response_text.find(self.client_response_endlist_tag) > 1 else False
        
        checker = None
        if not self._has_attr('client_response_check_when_running') is True and not self._has_attr('send_psn_message') is True:
            return
        
        if self._has_attr('client_response_check_when_running'):
            with self.bitrate_lock:
                # If checked client number is less than expected clients, add new client into check list
                client_ip = task.get_client_ip()
                if self.check_client_ip_dict.has_key(client_ip) and self.check_client_ip_dict[client_ip] is None:
                    self.check_client_ip_dict[client_ip] = CdvrBitrateResultTrace(task, self.client_response_ad_frequecy, self.client_response_content_segment_time, self.client_response_content_segment_number)
            
            # Same client, one index will do multiple bitrate requests, but only need record one bitrate trace
            if self.check_client_ip_dict.has_key(client_ip) and task.get_bitrate_url() == self.check_client_ip_dict[client_ip].bitrate_url:
                checker = CdvrManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag=self.client_response_media_tag, asset_id_tag=self.client_response_asset_tag)
                
                ad_url_list = checker.ad_url_list
                ad_number = checker.ad_ts_number
                entertainment_number = checker.entertainment_ts_number
                ad_position_list = checker.ad_mid_position_list
                bitrate_result = CdvrBitrateResult(task, time_util.get_local_now(), entertainment_number, ad_number, ad_url_list, ad_position_list)
                
                with self.bitrate_lock:
                    result_trace = self.check_client_ip_dict[client_ip]
                    result_trace.add_bitrate_result(bitrate_result)
                    if is_fixed_recording is True:
                        # if a recording is to end, mark it as fixed recording for future check 
                        result_trace.fixed()
                self.logger.info('Store bitrate response. %s' % (bitrate_result))
        
        if self._has_attr('send_psn_message') is True:
            if checker is None:
                checker = CdvrManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag=self.client_response_media_tag, asset_id_tag=self.client_response_asset_tag)
            
            psn_gap_list = [1 + int(self.client_response_content_segment_time * self.client_response_ad_ts_number * float(i)) for i in self.psn_message_sender_position]
            if self._has_attr('psn_send') is True:
                self.send_psn(task, checker.psn_tracking_position_id_dict, psn_gap_list)
        
        if is_fixed_recording is True:
            self._stop_bitrate_request_sched_task(task)
    
    def _stop_bitrate_request_sched_task(self, task):
        # If a cdvr recording is to end, remove its scheduled task, also remove it from alived client recorder dict
        if self.alived_client_recorder_dict.has_key(task.get_client_ip()):
            self.alived_client_recorder_dict.pop(task.get_client_ip())
        
        # If response content has endlist tag which meaning recoding is fixed, remove the its scheduled task
        job_name = self._generate_job_name(task)
        if self.job_recorder.has_key(job_name):
            self.logger.debug('Bitrate recording is fixed, remove task: %s' % (task))
            self.task_consumer_sched.unschedule_job(self.job_recorder.pop(job_name))
    
    def analysis_traced_bitrate_response(self):
        self.logger.debug('Analysis traced bitrate response. Checked client number is %s' % (self.check_client_ip_dict))
        for client_ip, bitrate_result_trace in self.check_client_ip_dict.items():
            self.do_bitrate_result_trace_check(client_ip, bitrate_result_trace)
    
    def do_bitrate_result_trace_check(self, client_ip, bitrate_result_trace):
        bitrate_result_trace.check(self.logger)
        
        if len(bitrate_result_trace.error_list) != 0:
            error_contents = client_ip + '::'
            error_contents += string.join(bitrate_result_trace.error_list, '||')
            self.error_record_queue.put(error_contents)
            bitrate_result_trace.error_list = []
            
        if bitrate_result_trace.validated is True:
            self._stop_bitrate_request_sched_task(bitrate_result_trace.task)
        
        if bitrate_result_trace.is_fixed is True or bitrate_result_trace.validated is True:
            self.check_client_ip_dict.pop(client_ip)
            self.logger.debug('Client %s has been checked, remove it from check list. Current check list size is %s' %(client_ip, len(self.check_client_ip_dict)))
    
    def _generate_job_name(self, task):
        m = hashlib.md5()
        task_info = '%s|%s' % (task.get_client_ip(), task.get_bitrate_url())
        m.update(task_info)
        value = m.hexdigest()
        return value
    
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
    pert_test = CdvrPerfTest(config_file, current_process_index, golden_config_file=golden_config_file)
    pert_test.run()
