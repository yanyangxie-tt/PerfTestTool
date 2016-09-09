# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import Queue
import string
import threading

from apscheduler.scheduler import Scheduler

from utility import common_util, vex_util
from utility.counter import Counter
from perf.test.model.perf_test import PerfTestBase

class VEXPerfTestBase(PerfTestBase):
    def __init__(self, config_file, log_file=None, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VEXPerfTestBase, self).__init__(config_file, log_file, **kwargs)
        self.init_environment()
        self.prepare_task()
        self.distribute_task()
    
    def init_environment(self):
        self.init_result_dir()
        self.init_log(self.result_dir + self.test_result_log_file, self.log_level)
        self.init_vex_counter()
        self.init_lock()
        self.init_queue()
        
        # init thread and threadpool
        self.init_task_sched()
        self.init_report_sched()
        self.init_psn_sched()
    
    def init_vex_counter(self, **kwargs):
        default_counter_list = '0,1000,3000,6000,12000'
        generate_counter = lambda couter_key, default: Counter(
                            [int(i) for i in string.split(
                                common_util.get_config_value_by_key(self.parameters, couter_key, default), ',')
                            ])
        
        self.index_response_counter = generate_counter('index.response.counter', default_counter_list)
        self.bitrate_response_counter = generate_counter('bitrate.response.counter', default_counter_list)
    
    def init_lock(self):
        self.index_lock = threading.RLock()
        self.bitrate_lock = threading.RLock()
    
    def init_queue(self):
        self.task_queue = Queue.Queue(10)
        self.bitrate_record_queue = Queue.Queue(10000)
        self.error_record_queue = Queue.Queue()
    
    def init_result_dir(self):
        self.process_number = self.parameters.get('process_number') if self.parameters.has_key('process_number') else 1 
        self.result_dir = vex_util.get_process_result_tmp_dir(self.test_result_temp_dir, self.test_case_name, self.process_number)
        self.test_result_report_delta_dir = self.result_dir + self.test_result_report_delta_dir
        self.test_result_report_error_dir = self.result_dir + self.test_result_report_error_dir
        self.test_result_report_traced_dir = self.result_dir + self.test_result_report_traced_dir
        print ('Result dir:%s, delta dir:%s, error dir:%s, traced dir:%s' 
                          % (self.result_dir, self.test_result_report_delta_dir, self.test_result_report_error_dir, self.test_result_report_traced_dir))
    
    def init_task_generater_and_dispatcher_thread(self):
        # 初始化生成worker task的线程. 在这个线程里，只是放task queue里放任务
        # 初始化消费task queue的线程。这个线程负责把任务往vod_sched中添加。根据warm-up和并发的数量，设计好每次读取queue中的数据量，然后给vod_sched,然后sleep 1秒
        pass
    
    def _init_apsched(self, gconfig):
        sched = Scheduler()
        sched.daemonic = True
        self.logger.debug('task schedule parameters: %s' % (gconfig))
        sched.configure(gconfig)
        return sched

    # def init_vod_sched(self):
    def init_task_sched(self):
        # 发request的线程池
        self._set_attr('task_apschdule_threadpool_core_threads', 100, False)
        self._set_attr('task_apschdule_threadpool_max_threads', 100, False)
        self._set_attr('task_apschdule_queue_max', 100000, False)
        self._set_attr('task_apschdule_tqueue_misfire_time', 300, False)
        
        gconfig = {'apscheduler.threadpool.core_threads':int(self.task_apschdule_threadpool_core_threads),
                   'apscheduler.threadpool.max_threads':int(self.task_apschdule_threadpool_max_threads),
                   'apscheduler.threadpool.keepalive':120,
                   'apscheduler.misfire_grace_time':int(self.task_apschdule_queue_max),
                   'apscheduler.coalesce':True,
                   'apscheduler.max_instances':int(self.task_apschdule_tqueue_misfire_time)}
        
        self.task_sched = self._init_apsched(gconfig)
        self.task_sched.start()
    
    def init_report_sched(self):
        gconfig = {'apscheduler.threadpool.core_threads':1, 'apscheduler.threadpool.max_threads':2, 'apscheduler.threadpool.keepalive':14400,
                   'apscheduler.misfire_grace_time':14400, 'apscheduler.coalesce':True, 'apscheduler.max_instances':50}
        
        self.report_sched = self._init_apsched(gconfig)
        self.report_sched.start()
    
    def init_psn_sched(self):
        self._set_attr('psn_apschdule_threadpool_core_threads', 100, False)
        self._set_attr('psn_apschdule_threadpool_max_threads', 100, False)
        self._set_attr('psn_apschdule_queue_max', 100000, False)
        self._set_attr('psn_apschdule_tqueue_misfire_time', 300, False)
        
        gconfig = {'apscheduler.threadpool.core_threads':int(self.psn_apschdule_threadpool_core_threads),
                   'apscheduler.threadpool.max_threads':int(self.psn_apschdule_threadpool_max_threads),
                   'apscheduler.threadpool.keepalive':120,
                   'apscheduler.misfire_grace_time':int(self.psn_apschdule_queue_max),
                   'apscheduler.coalesce':True,
                   'apscheduler.max_instances':int(self.psn_apschdule_tqueue_misfire_time)}
        
        self.psn_sched = self._init_apsched(gconfig)
        self.psn_sched.start()
    
    # 添加任务
    def prepare_task(self):
        pass
    
    def distribute_task(self):
        pass
