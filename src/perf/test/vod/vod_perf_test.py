# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import time
from requests.models import Response

from init_script_env import *
from perf.test.model.vex_perf_test import VEXPerfTestBase
from perf.test.parser.manifest import VODManifestChecker
from utility import time_util, manifest_util

class VODPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VODPerfTest, self).__init__(config_file, current_process_index=current_process_index, **kwargs)
    
    def set_compontent_private_default_value(self):
        self._set_attr('test_type_options', ['VOD_T6', 'OTHER:VOD'])
        self._set_attr('index_url_format', 'http://mm.vod.comcast.net/%s/king/index.m3u8?ProviderId=%s&AssetId=abcd1234567890123456&StreamType=%s&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00')
    
    # linear vod, cdvr do_index is the same
    def _get_fake_response(self, index=True):
        r = Response()
        response_text, status_code = ('no fake file', 200)
        
        fake_att_name = 'index-fake-response' if index else 'bitrate-fake-response'
        if hasattr(self, fake_att_name):
            response_text = getattr(self, fake_att_name)
        else:
            fake_dir = 'fake'
            fake_response_name = 'index-fake-response.txt' if index else 'bitrate-fake-response.txt'
            fake_response_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + '%s/%s' % (fake_dir, fake_response_name)
            if os.path.exists(fake_response_file):
                with open(fake_response_file) as f:
                    response_text = f.read()
                    setattr(self, fake_att_name, response_text)
        return r, 201, response_text, status_code
    
    def do_index(self, task):
        try:
            self.logger.debug('Execute index: %s' % (str(task)))
            if self._has_attr('use_fake_manifest') is True:
                response, used_time, response_text, status_code = self._get_fake_response(index=True)
            else:
                response, used_time = self._get_vex_response(task, tag='Index')
                response_text, status_code = response.text, response.status_code
                
            if response is None:
                self._increment_counter(self.index_counter, self.index_lock, response_time=used_time, is_error=True)
                return
            elif status_code != 200:
                self.logger.warn('Failed to index request. Status code:%s, message=%s, task:%s' % (response.status_code, response_text, task))
                self._increment_counter(self.index_counter, self.index_lock, response_time=used_time, is_error=True)
                return
            
            self._increment_counter(self.index_counter, self.index_lock, response_time=used_time, is_error=False)
            self.logger.debug('Index response for task[%s]:\n%s' % (task, response_text,))
            
            bitrate_url_list = manifest_util.get_bitrate_urls(response_text, self.test_bitrate_request_number)
            for i, bitrate_url in enumerate(bitrate_url_list):
                b_task = task.clone()
                delta_milliseconds = self.test_bitrate_serial_time * (i + 1) if self.test_bitrate_serial else self.test_bitrate_serial_time
                start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_milliseconds=delta_milliseconds)
                b_task.set_bitrate_url(bitrate_url)
                b_task.set_start_date(start_date)
                self.logger.debug('Schedule bitrate request at %s. task:%s' % (start_date, b_task))
                self.task_consumer_sched.add_date_job(self.do_bitrate, start_date, args=(b_task,))
        except Exception, e:
            self._increment_counter(self.index_counter, self.index_lock, response_time=0, is_error=True)
            self.logger.error('Failed to index request. %s' % (e), exc_info=1)
    
    # linear vod, cdvr do_bitrate, get_response之前都一样，可以提取公共的。接下来的check，linear和cdvr继续发送bitrate请求这里单独写    
    def do_bitrate(self, task):
        try:
            self.logger.debug('Execute bitrate: %s' % (str(task)))
            if self._has_attr('use_fake_manifest') is True:
                response, used_time, response_text, status_code = self._get_fake_response(index=False)
            else:
                response, used_time = self._get_vex_response(task, tag='Bitrate')
                response_text = response.text
                status_code = response.status_code
                
            if response is None:
                self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=used_time, is_error=True)
                return
            elif status_code != 200:
                self.logger.warn('Failed to bitrate request. Status code:%s, message=%s, task:%s' % (response.status_code, response_text, task))
                self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=used_time, is_error=True)
                return
            else:
                self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=used_time, is_error=False)
            
            if not self._has_attr('send_psn_message') and not self._has_attr('client_response_check_when_running'):
                return
            
            self.logger.debug('Bitrate response for task[%s]:\n%s' % (task, response_text,))
            checker = VODManifestChecker(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_')
            
            if self._has_attr('client_response_check_when_running'):
                self.check_response(task, checker)
            
            if self._has_attr('send_psn_message'):
                psn_gap_list = [1 + int(self.client_response_content_segment_time * self.client_response_ad_mid_roll_ts_number * float(i)) for i in self.psn_message_sender_position]
                if self._has_attr('psn_send') is True:
                    self.send_psn(task, checker.psn_tracking_position_id_dict, psn_gap_list)
                elif self._has_attr('psn_fake_send') is True:
                    self.send_psn(task, self.fake_psn_tracking_position_id_dict, psn_gap_list)
                
                if self._has_attr('psn_endall_send') is True:
                    self.send_endall_psn(task)
        except Exception, e:
            self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=0, is_error=True)
            self.logger.error('Failed to bitrate request. %s' % (e), exc_info=1)
        
    def check_response(self, task, manifest_checker):
        error_message = manifest_checker.check(self.client_response_media_sequence, self.client_response_content_segment_number,
                self.client_response_endlist_tag, self.client_response_drm_tag, self.client_response_ad_mid_roll_position, self.client_response_ad_pre_roll_ts_number,
                self.client_response_ad_mid_roll_ts_number, self.client_response_ad_post_roll_ts_number,)
        if error_message is not None and error_message != '':
            # self.logger.error('%s, Manifest:%s' % (error_message, manifest_checker.manifest))
            self.logger.error('%s' % (error_message))
            self.error_record_queue.put('%-17s: %s' % (task.get_client_ip(), error_message), False, 2)
        
    def _get_vex_response(self, task, tag='Index'):
        response, used_time = None, 0
        try:
            response, used_time = self.get_response(task, self.test_client_request_timeout)
        except Exception, e:
            self.logger.error('Failed to do %s task. %s. %s' % (tag, task, e), exc_info=0)
            
            mtries = self.test_client_request_retry_count
            retry_count = 1
            while mtries > 1:
                time.sleep(self.test_client_request_retry_delay)
                try:
                    self.logger.debug('Retry index, %s time. task:[%s]' % (retry_count, task))
                    response, used_time = self.get_response(task, self.test_client_request_timeout)
                    return response
                except Exception, e:
                    self.logger.error('Retry index failed, %s time. task:[%s]' % (retry_count, task))
                    mtries -= 1
        return response, used_time

    def task_generater(self):
        while True:
            if self.task_queue.full():
                self.logger.debug('Task queue is meet the max number %s, sleep 5 seconds' % (self.task_queue.maxsize))
                time.sleep(5)
                continue
            self.task_queue.put_nowait(self._generate_task())

    def dispatch_task(self):
        self.logger.debug('Start to dispatch task')
        if self.current_processs_concurrent_request_number == 0:
            self.logger.warn('Current request number for this process(%s) is 0, exit.' % (self.current_process_index))
            exit(0)
        
        if hasattr(self, 'test_warmup_period_minute'):
            warm_up_second_list = self._generate_warm_up_list()
            # generate warm-up rate
            if len(warm_up_second_list) > 0:
                self.logger.debug('Warm-up process, warm-up %s minute, warm rate %s' % (self.test_warmup_period_minute, [i for i in warm_up_second_list if i / 60 == 0]))
                # Fetch tasks by the number of warm_up_second_list, and then add it to task consumer(task sched)
                for task_number in warm_up_second_list:
                    self.logger.info('Warm-up stage: Put %s task into task queue' % (task_number))
                    index = 0
                    while index < task_number:
                        task = self.task_queue.get(True, timeout=10)
                        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=3)
                        task.set_start_date(start_date)
                        self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
                        index += 1
                    time.sleep(1)
        
        self.logger.debug('Start to do performance with max current request %s of this process' % (self.current_processs_concurrent_request_number))
        self.dispatch_task_sched.add_interval_job(self._fetch_task_and_add_to_consumer, seconds=1)
    
    def _fetch_task_and_add_to_consumer(self):
        # Fetch task from task queue, and add it to task consumer
        self.logger.debug('Put %s tasks into task schedule.' % (self.current_processs_concurrent_request_number))
        for i in range(0, self.current_processs_concurrent_request_number):
            try:
                task = self.task_queue.get(True, 6)
                start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=1)
                task.set_start_date(start_date)
                self.logger.debug('Task will be execute at %s. task:%s' % (start_date, task))
                self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
            except Exception, e:
                self.logger.error('Failed to fetch task from task queue', e)
    
    def _generate_warm_up_list(self):
        warm_up_period_minute = self._has_attr('test_warmup_period_minute')
        if not warm_up_period_minute:
            return []
        
        warm_up_second_list = []
        if warm_up_period_minute and warm_up_period_minute > 1:
            warm_up_minute_list = self._generate_warm_up_request_list(self.current_processs_concurrent_request_number, warm_up_period_minute)
            self.logger.info('Warm-up period is %s minute, warm-up list is:%s' % (warm_up_period_minute, warm_up_minute_list))
        else:
            self.logger.debug('Warm-up period is not set or its value <1, not do warm up')
            return []
        
        # to VOD, export warm up rate by seconds
        for t in warm_up_minute_list:
            for i in range(0, 1 * 60):
                warm_up_second_list.append(t)
        
        return warm_up_second_list

if __name__ == '__main__':
    current_process_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    # print 'current_process_index is %s' % (current_process_index)
    
    here = os.path.dirname(os.path.realpath(__file__))
    config_file = here + os.sep + 'config.properties'
    golden_config_file = here + os.sep + 'config-golden.properties'
    
    pert_test = VODPerfTest(config_file, current_process_index, golden_config_file=golden_config_file)
    pert_test.run()
