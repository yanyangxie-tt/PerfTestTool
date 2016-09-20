# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import Queue
import logging
import os
import random
import sys
import threading
import time
import traceback

from apscheduler.scheduler import Scheduler
from requests.models import Response

from perf.test.model.configuration import Configurations
from perf.test.model.psn import PSNEvents
from perf.test.model.task import VEXScheduleReqeustsTask
from perf.test.model.vex_counter import VEXMetricCounter
from perf.test.model.vex_requests import VEXRequest
from utility import vex_util, time_util, logger_util, ip_util, file_util, common_util


class VEXPerfTestBase(Configurations, VEXRequest, PSNEvents):
    def __init__(self, config_file, current_process_index=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param current_process_index: current process number, should less than your max process executer number
        '''
        super(VEXPerfTestBase, self).__init__(config_file, **kwargs)
        self.init_current_process_index(current_process_index)
        self.init_environment()
        self.init_sched()
        self.init_load_test_start_date()
    
    def init_configured_parameters_default_value(self):
        # setup default value of performance test
        self.set_vex_common_default_value()
        self.set_component_private_default_value()
    
    def set_vex_common_default_value(self):
        # setup default value of parameters in common for both vod,cdvr and linear 
        self._set_attr('test_case_survival', 600)
        self._set_attr('test_result_report_dir', '/tmp/load-test-result')
        
        # Default value of log.export.thirdparty is False, not to export thirdparty logs.
        if self._has_attr('log_export_thirdparty') and getattr(self, 'log_export_thirdparty') is True:
            self._set_attr('log_name', None)
        else:
            self._set_attr('log_name', 'vex')
            
        self._set_attr('test_client_zone_number', 500)
        self._set_attr('test_client_location_number', 500)
        
        self._set_attr('test_client_request_timeout', 7)
        self._set_attr('test_client_request_retry_count', 3)
        self._set_attr('test_client_request_retry_delay', 1)
        
        self._set_attr('test_bitrate_request_number', 1)
        self._set_attr('test_bitrate_serial', False)
        self._set_attr('test_bitrate_serial_time', 300)
        
        self._set_attr('test_result_log_file', 'load-test.log')
        self._set_attr('test_execute_process_number', 1)
        
        self._set_attr('psn_send', False)
        self._set_attr('psn_fake_send', False)
        self._set_attr('psn_endall_send', False)
        
        # thread pool parameters: task consumer
        self._set_attr('task_apschdule_threadpool_core_threads', 100, False)
        self._set_attr('task_apschdule_threadpool_max_threads', 100, False)
        self._set_attr('task_apschdule_queue_max', 100000, False)
        self._set_attr('task_apschdule_tqueue_misfire_time', 300, False)
        
        if hasattr(self, 'test_client_vip_latest_segment_range'):
            self.ip_segment_range = vex_util.get_test_client_ip_latest_segment_range(self.test_client_vip_latest_segment_range)
        else:
            self.ip_segment_range = [i for i in range(0, 256)]
    
    def set_component_private_default_value(self):
        # should setup component default parameters
        pass
    
    def init_current_process_index(self, process_index):
        if type(process_index) is not int:
            raise Exception('current_process_index must be int')
        
        if process_index not in range(0, self.test_execute_process_number):
            raise Exception('Current process index must be less than the execute process size %s')
        self.current_process_index = process_index
    
    def init_environment(self):
        self.init_result_dir()
        self.init_log(log_file=self.test_result_dir + self.test_result_log_file, log_level=self.log_level, log_name=self.log_name)
        self.init_vex_counter()
        self.init_lock()
        self.init_queue()
        self.setup_test_machine_conccurent_request_number()
        self.setup_processs_concurrent_request_number()
        self.setup_test_contents()
    
    def init_result_dir(self):
        # To multiple process, each process has its private log， need use a flag to generate its private result dir. Now we use current_process_index
        self.test_result_dir = vex_util.get_process_result_tmp_dir(self.test_result_report_dir, self.test_case_name, self.current_process_index)
        self.test_result_report_delta_dir = self.test_result_dir + self.test_result_report_delta_dir
        self.test_result_report_error_dir = self.test_result_dir + self.test_result_report_error_dir
        self.test_result_report_traced_dir = self.test_result_dir + self.test_result_report_traced_dir

    def init_log(self, log_file, log_level, log_name=None):
        logger_util.setup_logger(log_file, name=log_name, log_level=log_level)
        self.logger = logging.getLogger(name=log_name)
    
    def init_sched(self):
        self.init_task_consumer_sched()
        self.init_task_dispatcher_sched()
        self.init_report_sched()
        self.init_psn_sched()
        
    def init_load_test_start_date(self):
        # record the start time of perf test
        self.load_test_start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=2)
    
    def init_vex_counter(self, **kwargs):
        # initial response time metric object for both index and bitrate 
        default_counters = [0, 1000, 3000, 6000, 12000]
        generate_counter = lambda att, default_value: VEXMetricCounter(getattr(self, att) if self._has_attr(att) else default_value, name=att)
        setattr(self, 'index_counter', generate_counter('index_response_counter', default_counters))
        setattr(self, 'bitrate_counter', generate_counter('bitrate_response_counter', default_counters))
    
    def init_lock(self):
        self.index_lock = threading.RLock()
        self.bitrate_lock = threading.RLock()
    
    def init_queue(self):
        self.task_queue = Queue.Queue(10000)
        self.bitrate_record_queue = Queue.Queue(10000)
        self.error_record_queue = Queue.Queue(100000)
    
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
        # if self.psn_send or self.psn_fake_send or self.psn_endall_send:
        if self._has_attr('psn_send') is True or self._has_attr('psn_fake_send') is True or self._has_attr('psn_endall_send') is True:
            self.send_psn_message = True
            PSNEvents.__init__(self, self.logger)
            
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
            
            if self._has_attr('psn_fake_position') and self._has_attr('psn_fake_tracking_id'):
                self.psn_fake_tracking_position_id_dict = {int(psn_position):self.psn_fake_tracking_id for psn_position in self.psn_fake_position}
            else:
                self.psn_fake_tracking_position_id_dict = {}
    
    def setup_test_machine_conccurent_request_number(self):
        # for distribute perf test, calculate concurrent request number in one test machine
        if not hasattr(self, 'test_machine_hosts'):
            self.logger.fatal('test.machine.hosts must be configured.')
            exit(1)
        
        if type(self.test_machine_hosts) is not list:
            self.test_machine_hosts = self.test_machine_hosts.split(',')
        test_machine_inistace_size = len(self.test_machine_hosts)
        self.test_machine_current_request_number = self.test_case_concurrent_number / test_machine_inistace_size if self.test_case_concurrent_number > test_machine_inistace_size else 1
    
    def setup_processs_concurrent_request_number(self):
        # for multiple process, calculate concurrent request number in one process
        current_number, remainder = divmod(self.test_machine_current_request_number, self.test_execute_process_number)
        if self.current_process_index < remainder:
            current_number += 1
       
        self.current_processs_concurrent_request_number = current_number
    
    def setup_test_contents(self):
        # setup all the test content
        if not hasattr(self, 'test_case_content_names'):
            self.logger.fatal('Test content names must be set. for example: "test.case.content.names=vod_test_[1~100]"')
            exit(1)
        
        self.test_content_name_list = vex_util.get_test_content_name_list(self.test_case_content_names, offset=0)
        if len(self.test_content_name_list) > 1:
            self.logger.info('Test content names are from %s to %s' % (self.test_content_name_list[0], self.test_content_name_list[-1]))
        else:
            self.logger.info('Test content name is %s' % (self.test_content_name_list[0]))
    
    def _use_fake(self):
        # whether to use fake response
        return self._has_attr('test_use_fake_manifest')
    
    def _get_fake_response(self, fake_response_file, fake_file_att_name='fake_response'):
        # read fake file as http fake response 
        r = Response()
        response_text, status_code = ('fake response content', 200)
        
        if hasattr(self, fake_file_att_name):
            response_text = getattr(self, fake_file_att_name)
        else:
            if os.path.exists(fake_response_file):
                with open(fake_response_file) as f:
                    response_text = f.read()
                    setattr(self, fake_file_att_name, response_text)
            else:
                self.logger.error('not found fake file %s' % (fake_response_file))
        return r, 201, response_text, status_code
    
    def _get_vex_response(self, task, tag='Index'):
        # get vex response. If failed, retry 'test_client_request_retry_count' times
        # return response and response time
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
    
    def send_psn(self, task, psn_tracking_position_id_dict, psn_gap_list):
        if psn_tracking_position_id_dict is None or len(psn_tracking_position_id_dict) == 0:
            return
        
        try:
            psn_event_list = self.generate_psn_scheduled_event_list(psn_tracking_position_id_dict, psn_gap_list, segment_time=self.client_response_content_segment_time)
            self.logger.debug('PSN event list is:%s' % (str(psn_event_list)))
            self.schedule_psn_event(self.psn_sched, psn_event_list, task.get_client_ip(), self.psn_receiver_host, self.psn_receiver_port, tag='normal')
        except:
            exce_info = 'Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
            self.logger.error("Failed to send normal PSN message. Exception: %s." % (exce_info))
    
    def send_endall_psn(self, task):
        try:
            matched_sid = common_util.matched_string(task.get_bitrate_url(), '&sid=([^&]*)')
            sid = matched_sid[0] if matched_sid is not None and len(matched_sid) > 0 else None
            if sid:
                self.schedule_end_all_psn_event(self.psn_sched, sid, self.psn_endall_position, self.psn_receiver_host, self.psn_receiver_port, tag='endall')
        except:
            exce_info = 'Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
            self.logger.error("Failed to send normal PSN message. Exception: %s." % (exce_info))
    
    def dump_summary_statistical_data(self):
        cost_time = time_util.get_time_gap_in_seconds(time_util.get_local_now(), self.load_test_start_date)
        index_statistical_data = self.index_counter.dump_counter_info(cost_time, delta=False, tag='Index response summary')
        bitrate_statistical_data = self.bitrate_counter.dump_counter_info(cost_time, delta=False, tag='Bitrate response summary')
        statistical_data = index_statistical_data + '\n' + bitrate_statistical_data
        self.logger.info('Export load test report file to %s/%s at %s' % (self.test_result_dir, self.test_result_report_file, time_util.get_local_now()))
        # self.logger.info(statistical_data)
        file_util.write_file(self.test_result_dir, self.test_result_report_file, statistical_data, mode='a', is_delete=True)
    
    def dump_delta_statistical_data(self):
        index_statistical_data = self.index_counter.dump_counter_info(self.test_case_counter_dump_interval, delta=True, tag='Index response summary')
        bitrate_statistical_data = self.bitrate_counter.dump_counter_info(self.test_case_counter_dump_interval, delta=True, tag='Bitrate response summary')
        statistical_data = index_statistical_data + '\n' + bitrate_statistical_data
        
        self.index_counter.clear_delta_metric()
        self.bitrate_counter.clear_delta_metric()
        
        delta_report_file = vex_util.get_timed_file_name(self.test_result_report_delta_file)
        self.logger.debug('Export delta load test report file to %s/%s at %s' % (self.test_result_report_delta_dir, delta_report_file, time_util.get_local_now()))
        self.logger.info(statistical_data)
        file_util.write_file(self.test_result_report_delta_dir, delta_report_file, statistical_data, mode='a', is_delete=True)
        
        if self._has_attr('psn_count'):
            with self.psn_lock:
                self.logger.info('PSN count: %s, endAll PSN count: %s' % (self.psn_count, self.endall_psn_count))
                self.psn_count, self.endall_psn_count = (0, 0)
    
    def dump_delta_error_details(self):
        if self.error_record_queue.empty():
            return
        
        datas = vex_util.get_datas_in_queue(self.error_record_queue)
        delta_error_file = vex_util.get_timed_file_name(self.test_result_report_error_file)
        self.logger.info('Export delta error report file to %s/%s at %s' % (self.test_result_report_error_dir, delta_error_file, time_util.get_local_now()))
        file_util.write_file(self.test_result_report_error_dir, delta_error_file, datas, mode='a', is_delete=True)
    
    def dump_traced_bitrate_contents(self):
        if self.bitrate_record_queue.empty():
            return

        datas = vex_util.get_datas_in_queue(self.bitrate_record_queue)
        delta_traced_file = vex_util.get_timed_file_name(self.test_result_report_traced_file)
        self.logger.info('Export delta traced report file to %s/%s at %s' % (self.test_result_report_traced_dir, delta_traced_file, time_util.get_local_now()))
        file_util.write_file(self.test_result_report_traced_dir, delta_traced_file, datas, mode='a', is_delete=True)
     
    def startup_reporter(self):
        if hasattr(self, 'test_case_counter_dump_interval'):
            self.logger.debug('Dump statistical data while running each %s seconds' % (self.test_case_counter_dump_interval))
            r_start_date = time_util.get_datetime_after(self.load_test_start_date, delta_seconds=self.test_case_counter_dump_interval)
            self.report_sched.add_interval_job(self.dump_summary_statistical_data, seconds=self.test_case_counter_dump_interval, start_date=r_start_date)
            self.report_sched.add_interval_job(self.dump_delta_statistical_data, seconds=self.test_case_counter_dump_interval, start_date=r_start_date)
            self.report_sched.add_interval_job(self.dump_delta_error_details, seconds=self.test_case_counter_dump_interval, start_date=r_start_date)
            self.report_sched.add_interval_job(self.dump_traced_bitrate_contents, seconds=self.test_case_counter_dump_interval, start_date=r_start_date)
        else:
            self.logger.warn('No parameter test.case.counter.dump.interval, not dump statistical data while running')
            
    def prepare_task(self):
        self.logger.debug('Start to prepare task')
        self.task_generater = threading.Thread(target=self.task_generater)
        self.task_generater.setDaemon(True)
        self.task_generater.start()
    
    def task_generater(self):
        pass
    
    def dispatch_task(self):
        pass
    
    def _get_random_content(self):
        i = random.randint(0, len(self.test_content_name_list) - 1)
        return self.test_content_name_list[i]
    
    def _get_random_zone(self):
        i = random.randint(0, self.test_client_zone_number)
        return 'zone-%s' % (i)
    
    def _get_random_location(self):
        i = random.randint(0, self.test_client_location_number)
        return 'location-%s' % (i)
    
    def _get_test_type(self):
        if not hasattr(self, 'test_case_type'):
            self.logger.fatal('Test case type must be set. for example: "test.case.type=VOD_T6"')
            exit(1)
        return self.test_case_type
    
    def _generate_task(self):
        content_name = self._get_random_content()
        
        if self._has_attr('test_type_options'):
            if self.test_case_type not in self.test_type_options:
                self.logger.fatal('Test type %s in not in %s' % (self.test_case_type, self.test_type_options))
                exit(1)
        
        index_url = self.index_url_format % (content_name, content_name, self.test_case_type)
        client_ip = ip_util.generate_random_ip(ip_segment_range=self.ip_segment_range)
        location = self._get_random_location()
        zone = self._get_random_zone()
        return VEXScheduleReqeustsTask(index_url, client_ip, location, zone)
    
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
    
    def _increment_counter(self, counter_obj, counter_lock, response_time=0, is_error_request=False, is_error_response=False):
        with counter_lock:
            if is_error_request:
                counter_obj.increment_error()
            elif is_error_response:
                counter_obj.increment_error_response()
            else:
                counter_obj.increment(response_time)

    def run(self):
        try:
            self.logger.info('Start to do performance test at %s' % (time_util.get_local_now()))
            self.startup_reporter()
            self.prepare_task()
            self.dispatch_task()
            
            while(True):
                time.sleep(1)
                current_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=0)
                if time_util.get_time_gap_in_seconds(current_date, self.load_test_start_date) >= self.test_case_survival:
                    break
            
            self.logger.info('#' * 100)
            self.logger.info('Reach load test time limitation %s. Shutdown sched and flush statistics info into local file.' % (self.test_case_survival))
            self.dispatch_task_sched.shutdown(False)
            self.task_consumer_sched.shutdown(True)
            self.report_sched.shutdown(False)
            if self.send_psn_message: 
                self.psn_sched.shutdown(False)
            
            self.dump_summary_statistical_data()
            self.dump_traced_bitrate_contents()
            self.dump_delta_error_details()
            self.logger.info('Load test finished at %s' % (current_date))
        except Exception, e:
            exc_type, exc_value, exc_tb = sys.exc_info() 
            traceback.print_exception(exc_type, exc_value, exc_tb)
            self.logger.fatal('Fatal exception occurs, stop the load test.', e)
