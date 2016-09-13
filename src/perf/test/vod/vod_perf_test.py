# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import time

from perf.test.model.vex_perf_test import VEXPerfTestBase
from utility import time_util, manifest_util

class VODPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_number=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VODPerfTest, self).__init__(config_file, current_process_index=current_process_number, **kwargs)
    
    def set_compontent_private_default_value(self):
        self._set_attr('test_type_options', ['VOD_T6', 'OTHER:VOD'])
        self._set_attr('index_url_format', 'http://mm.vod.comcast.net/%s/king/index.m3u8?ProviderId=%s&AssetId=abcd1234567890123456&StreamType=%s&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00')
    
    # counter 尝试采用切面？
    def do_index(self, task):
        self.logger.debug('Execute index: %s' % (str(task)))
        response = self._get_vex_response(task, tag='Index')
        response_text = response.text
        
        if response is None:
            return
        elif response.status_code != 200:
            self.logger.warn('Failed to index request. Status code:%s, message=%s, task:%s' % (response.status_code, response_text, task))
            return
        else:
            self.logger.debug('%s, Index response for task[%s]:\n%s' % (response.status_code, task, response_text,))
        
        bitrate_url_list = manifest_util.get_bitrate_urls(response_text)
        for bitrate_url in bitrate_url_list:
            b_task = task.clone()
            start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_milliseconds=200)
            b_task.set_bitrate_url(bitrate_url)
            b_task.set_start_date(start_date)
            self.logger.debug('Schedule bitrate request. task:%s' % (b_task))
            self.task_consumer_sched.add_date_job(self.do_bitrate, start_date, args=(b_task,))
        
    def do_bitrate(self, task):
        self.logger.debug('Execute bitrate: %s' % (str(task)))
        response = self._get_vex_response(task, tag='Bitrate')
        if response is None:
            return
        
        response_text = response.text
        self.logger.debug('Bitrate response for task[%s]:\n%s' % (task, response_text,))
    
    # 将来用decrator代替
    def _get_vex_response(self, task, tag='Index'):
        response = None
        try:
            response = self.get_response(task, self.test_client_request_timeout)
        except Exception, e:
            self.logger.error('Failed to do %s task. %s' % (tag, task,), e)
            
            mtries = self.test_client_request_retry_count
            retry_count = 1
            while mtries > 1:
                time.sleep(self.test_client_request_retry_delay)
                try:
                    self.logger.debug('Retry index, %s time. task:[%s]' % (retry_count, task))
                    response = self.get_response(task, self.test_client_request_timeout)
                    return response
                except Exception, e:
                    self.logger.error('Retry index failed, %s time. task:[%s]' % (retry_count, task))
                    mtries -= 1
        return response

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
            self.logger.warn('Current request number for this process(%s) is 0, exit.' % (self.current_process_number))
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
    here = os.path.dirname(os.path.realpath(__file__))
    
    config_file = here + os.sep + 'config.properties'
    golden_config_file = here + os.sep + 'config-golden.properties'
    
    v = VODPerfTest(config_file, golden_config_file=golden_config_file)
    v.run()
