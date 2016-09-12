# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import Queue
import string
import threading
import time

from apscheduler.scheduler import Scheduler

from perf.test.model.perf_test import PerfTestBase
from utility import vex_util, time_util
from utility.counter import Counter


class VEXPerfTestBase(PerfTestBase):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param current_process_index: current process number, should less than your max process executer number
        '''
        super(VEXPerfTestBase, self).__init__(config_file, **kwargs)
        self.init_current_process_index(current_process_index)
        self.init_environment()
        self.init_sched()
    
    def init_configred_parameters_default_value(self):
        # Default value of log.export.thirdparty is False, not to export thirdparty logs.
        if self._has_attr('log_export_thirdparty') and getattr(self, 'log_export_thirdparty'):
            self._set_attr('log_name', 'vex')
        else:
            self._set_attr('log_name', None)
        
        self._set_attr('test_result_log_file', 'load-test.log')
        self._set_attr('test_execute_process_number', 1)
        
        self._set_attr('psn_send', False)
        self._set_attr('psn_fake_send', False)
        self._set_attr('psn_endall_send', False)
        
        # threadpool parameters: task consumer
        self._set_attr('task_apschdule_threadpool_core_threads', 100, False)
        self._set_attr('task_apschdule_threadpool_max_threads', 100, False)
        self._set_attr('task_apschdule_queue_max', 100000, False)
        self._set_attr('task_apschdule_tqueue_misfire_time', 300, False)
    
    def init_current_process_index(self, process_index):
        if type(process_index) is not int:
            raise Exception('current_process_index must be int')
        
        if process_index not in range(0, self.test_execute_process_number):
            raise Exception('Current process index must be less than the execute process size %s')
        self.current_process_index = process_index
    
    def init_environment(self):
        self.init_result_dir()
        self.init_log(self.result_dir + self.test_result_log_file, self.log_level, self.log_name)
        self.init_vex_counter()
        self.init_lock()
        self.init_queue()
        self.set_test_machine_conccurent_request_number()
        self.set_processs_concurrent_request_number()
    
    def init_sched(self):
        self.init_task_consumer_sched()
        self.init_task_dispatcher_sched()
        self.init_report_sched()
        self.init_psn_sched()
    
    def init_vex_counter(self, **kwargs):
        default_counters = '0,1000,3000,6000,12000'
        generate_counter = lambda default_value: Counter([int(i) for i in string.split(default_value, ',')])
        if not self._has_attr('index_response_counter'):
            setattr(self, 'index_response_counter', generate_counter(default_counters))
            
        if not self._has_attr('bitrate_response_counter'):
            setattr(self, 'bitrate_response_counter', generate_counter(default_counters))
    
    def init_lock(self):
        self.index_lock = threading.RLock()
        self.bitrate_lock = threading.RLock()
    
    def init_queue(self):
        self.task_queue = Queue.Queue(10000)
        self.bitrate_record_queue = Queue.Queue(10000)
        self.error_record_queue = Queue.Queue(100000)
    
    def init_result_dir(self):
        # To multiple process, each process has its private log， need use a flag to generate its private result dir. Now we use current_process_index
        self.result_dir = vex_util.get_process_result_tmp_dir(self.test_result_temp_dir, self.test_case_name, self.current_process_index)
        self.test_result_report_delta_dir = self.result_dir + self.test_result_report_delta_dir
        self.test_result_report_error_dir = self.result_dir + self.test_result_report_error_dir
        self.test_result_report_traced_dir = self.result_dir + self.test_result_report_traced_dir

    # def init_vod_sched(self):
    def init_task_consumer_sched(self):
        gconfig = {'apscheduler.threadpool.core_threads':self.task_apschdule_threadpool_core_threads,
                   'apscheduler.threadpool.max_threads':self.task_apschdule_threadpool_max_threads,
                   'apscheduler.threadpool.keepalive':120,
                   'apscheduler.misfire_grace_time':self.task_apschdule_queue_max,
                   'apscheduler.coalesce':True,
                   'apscheduler.max_instances':self.task_apschdule_tqueue_misfire_time}
        
        self.task_consumer_sched = self._init_apsched(gconfig)
        self.task_consumer_sched.start()
    
    def init_task_dispatcher_sched(self):
        gconfig = {'apscheduler.threadpool.core_threads':1, 'apscheduler.threadpool.max_threads':2, 'apscheduler.threadpool.keepalive':14400,
                   'apscheduler.misfire_grace_time':14400, 'apscheduler.coalesce':True, 'apscheduler.max_instances':50}
        
        self.dispatch_task_sched = self._init_apsched(gconfig)
        self.dispatch_task_sched.start()
    
    def init_report_sched(self):
        gconfig = {'apscheduler.threadpool.core_threads':1, 'apscheduler.threadpool.max_threads':2, 'apscheduler.threadpool.keepalive':14400,
                   'apscheduler.misfire_grace_time':14400, 'apscheduler.coalesce':True, 'apscheduler.max_instances':50}
        
        self.report_sched = self._init_apsched(gconfig)
        self.report_sched.start()
    
    def init_psn_sched(self):
        if self.psn_send or self.psn_fake_send or self.psn_endall_send:
            # self.logger.debug('Init PSN scheduler. send psn:%s, send fake psn:%s, send end all:%s' % (self.psn_send, self.self.psn_fake_send, self.psn_endall_send))
            self._set_attr('psn_apschdule_threadpool_core_threads', 100, False)
            self._set_attr('psn_apschdule_threadpool_max_threads', 100, False)
            self._set_attr('psn_apschdule_queue_max', 100000, False)
            self._set_attr('psn_apschdule_tqueue_misfire_time', 300, False)
            
            gconfig = {'apscheduler.threadpool.core_threads':self.psn_apschdule_threadpool_core_threads,
                       'apscheduler.threadpool.max_threads':self.psn_apschdule_threadpool_max_threads,
                       'apscheduler.threadpool.keepalive':120,
                       'apscheduler.misfire_grace_time':self.psn_apschdule_queue_max,
                       'apscheduler.coalesce':True,
                       'apscheduler.max_instances':self.psn_apschdule_tqueue_misfire_time}
            
            self.psn_sched = self._init_apsched(gconfig)
            self.psn_sched.start()
    
    def set_test_machine_conccurent_request_number(self):
        if not hasattr(self, 'test_machine_hosts'):
            self.logger.error('test.machine.hosts must be configured.')
            exit(1)
        
        test_machine_inistace_size = len(self.test_machine_hosts)
        self.test_machine_current_request_number = self.test_client_concurrent_number / test_machine_inistace_size if self.test_client_concurrent_number > test_machine_inistace_size else 1
    
    def set_processs_concurrent_request_number(self):
        current_number, remainder = divmod(self.test_machine_current_request_number, self.test_execute_process_number)
        if self.current_process_index < remainder + 1:
            current_number += 1
       
        self.current_processs_concurrent_request_number = current_number
    
    def prepare_task(self):
        self.logger.debug('Start to prepare task')
        self.task_generater = threading.Thread(target=self.task_generater)
        self.task_generater.setDaemon(True)
        self.task_generater.start()
    
    def task_generater(self):
        pass
    
    def dispatch_task(self):
        pass
    
    def run(self):
        print '#' * 100
        self.logger.info('Start to do performance test at %s' % (time_util.get_local_now()))
        self.prepare_task()
        self.dispatch_task()
        
        time.sleep(10)
        self.logger.info('#' * 100)
        self.logger.info('Finish to do performance test at %s' % (time_util.get_local_now()))
    
    def _generate_warm_up_request_list(self, total_number, warm_up_period_minute):
        increased_per_second = total_number / warm_up_period_minute if total_number > warm_up_period_minute else 1

        warm_up_minute_list = []
        tmp_number = increased_per_second
        while True:
            if tmp_number <= total_number:
                warm_up_minute_list.append(tmp_number)
                tmp_number += increased_per_second
            else:
                break
        return warm_up_minute_list
    
    def _init_apsched(self, gconfig):
        sched = Scheduler()
        sched.daemonic = True
        self.logger.debug('task schedule parameters: %s' % (gconfig))
        sched.configure(gconfig)
        return sched
