# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import Queue
import os
import string
import sys
import threading

sys.path.append(os.path.join(os.path.split(os.path.realpath(__file__))[0], "../.."))
from perf.test.model.perf_test import APIPerfTestBase
from utility import common_util
from utility.counter import Counter

class VEXPerfTestBase(APIPerfTestBase):
    def __init__(self, config_file, log_file, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VEXPerfTestBase, self).__init__(config_file, log_file, **kwargs)
        self.result_dir = 'result_dir'
    
    def init_environment(self):
        self.init_configred_parameters()
        self.init_vex_counter()
        self.init_lock()
        self.init_recorder()
        self.init_result_dir()
    
    def init_configred_parameters(self):
        ''' Read configured parameters and then set general parameters as object attribute '''
        print '#' * 100
        print 'Initial general performance test parameters from configuration file %s' % (self.config_file)
        set_attr = lambda attr_name, config_name, default_value = None: self._set_attr(attr_name, common_util.get_config_value_by_key(self.parameters, config_name, default_value))
        
        set_attr('user', 'user', 'root')
    
    def init_vex_counter(self, **kwargs):
        default_counter_list = '0,200,500,1000,2000,3000,4000,5000,6000,12000'
        generate_counter = lambda couter_key, default: Counter(
                            [int(i) for i in string.split(
                                common_util.get_config_value_by_key(self.parameters, couter_key, default), ',')
                            ])
        self.index_response_counter = generate_counter('index.counter', default_counter_list)
        self.bitrate_response_counter = generate_counter('bitrate.counter', default_counter_list)
    
    def init_lock(self):
        self.index_lock = threading.RLock()
        self.bitrate_lock = threading.RLock()
    
    def init_recorder(self):
        self.bitrate_recorder = Queue.Queue()  # will be exported to local after delta report
        self.error_recorder = Queue.Queue()
    
    def init_result_dir(self):
        test_case_name = common_util.get_config_value_by_key(self.parameters, 'test_case_name')
        # result_dir = common_util.get_process_result_tmp_dir(process_number, constants.result_dir, test_case_name)
    
    def demo(self):
        self.index_response_counter.increment(200)
        print self.index_response_counter.dump()
        print self.logger
        print dir(self.logger)
        print self.logger.level
        print self.logger.name
        self.logger.info('1234')
        self.logger.debug('debug')
           
    
