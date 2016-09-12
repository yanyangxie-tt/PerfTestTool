# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import time

from perf.test.model.task import VEXScheduleReqeustsTask
from perf.test.model.vex_perf_test import VEXPerfTestBase
from utility import time_util


class VODPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_number=1, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VODPerfTest, self).__init__(config_file, current_process_index=current_process_number, **kwargs)

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
            warm_up_second_list, warm_up_minute_list = self._generate_warm_up_list()
            # generate warm-up rate
            if len(warm_up_second_list) > 0:
                self.logger.debug('Warm-up process, warm-up minute is %s, warm rate %s' % (self.test_warmup_period_minute, self.warm_up_minute_list))
                # Fetch tasks by the number of warm_up_second_list, and then add it to task consumer(task sched)
                for task_number in warm_up_second_list:
                    self.logger.info('Warm-up stage: Put %s task into task queue' % (task_number))
                    index = 0
                    while index < task_number:
                        task = self.task_queue.get(True, timeout=10)
                        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=3)
                        task.set_start_date(start_date)
                        self.task_consumer_sched.add_date_job(self.do_vod_asset_call, start_date, args=(task))
                        index += 1
                    time.sleep(1)
        
        self.logger.debug('Start to do performance with max current request %s of this process' % (self.current_processs_concurrent_request_number))
        self.dispatch_task_sched.add_interval_job(self._fetch_task_and_add_to_consumer, seconds=1)
    
    def do_vod_asset_call(self, task):
        self.logger.info('exeute task in %s' % (task.get_start_date()))
    
    def _generate_task(self):
        # generate task by VOD url formatter
        task = VEXScheduleReqeustsTask('http://www.baidu.com', '192.168.1.1', 'zone1', 'location1')
        return task
    
    def _fetch_task_and_add_to_consumer(self):
        # Fetch task from task queue, and add it to task consumer
        self.logger.debug('Put %s tasks into task schedule.' % (self.current_processs_concurrent_request_number))
        for i in range(0, self.current_processs_concurrent_request_number):
            try:
                task = self.task_queue.get(True, 6)
                
                # schedule a new event for index request
                start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=1)
                # self.logger.debug('Put one task onto task schedule')
                
                # 这行有问题
                self.task_consumer_sched.add_date_job(self.do_vod_asset_call, start_date, args=(task,))
            except Exception, e:
                self.logger.error('Failed to fetch task from task queue', e)
    
    def _generate_warm_up_list(self):
        warm_up_period_minute = self._has_attr('test_warmup_period_minute')
        if not warm_up_period_minute:
            return []
        
        warm_up_minute_list, warm_up_second_list = [], []
        if warm_up_period_minute and warm_up_period_minute > 1:
            warm_up_minute_list = self._generate_warm_up_request_list(self.current_processs_concurrent_request_number, warm_up_period_minute)
            self.logger.info('Warm-up period is %s minute, warm-up list is:%s' % (warm_up_period_minute, warm_up_minute_list))
        else:
            self.logger.debug('Warm-up period is not set or its value <1, not do warm up')
            return [], []
        
        # to VOD, export warm up rate by seconds
        for t in warm_up_minute_list:
            for i in range(0, 1 * 60):
                warm_up_second_list.append(t)
        
        return warm_up_second_list, warm_up_minute_list

if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    
    config_file = here + os.sep + 'config.properties'
    golden_config_file = here + os.sep + 'config-golden.properties'
    
    v = VODPerfTest(config_file, golden_config_file=golden_config_file)
    v.run()
