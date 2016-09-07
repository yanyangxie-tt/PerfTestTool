# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import string
import sys

from utility import common_util, logger_util
from utility.counter import Counter
import logging


sys.path.append(os.path.join(os.path.split(os.path.realpath(__file__))[0], "../.."))

log_level_key = 'log.level'
index_counter_key = 'index.counter'
bitrate_counter_key = 'bitrate.counter'

class PerfTestBase(object):
    '''
    Basic module for performance test
    '''
    def __init__(self, config_file, log_file, log_level='DEBUG', **kwargs):
        '''Initialized configuration and logs with a properties file and log file'''
        self.config_file = config_file
        self.log_file = log_file
        self.log_level = log_level
        
        if not os.path.exists(self.config_file):
            print 'Configuration file %s do not exist' % (self.config_file)
            sys.exit(1)
            
        self.parameters = common_util.load_properties(self.config_file)
        self.parameters.update(kwargs)
        
        if self.parameters.has_key(log_level_key):
            self.log_file = self.parameters.get(log_level_key)
        self.init_log()

    def init_log(self):
        logger_util.setup_logger(self.log_file, log_level=self.log_level)

    def _has_attr(self, attr_name):
        if not hasattr(self, attr_name):
            return False
        else:
            return getattr(self, attr_name, None)

    def _set_attr(self, attr_name, attr_value):
        setattr(self, attr_name, attr_value)

class VEXPerfTestBase(PerfTestBase):
    def __init__(self, config_file, log_file, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VEXPerfTestBase, self).__init__(config_file, log_file, **kwargs)
        self.logger = logging.getLogger()
        self.init_vex_counter()
    
    def init_vex_counter(self, **kwargs):
        default_counter_list = '0,200,500,1000,2000,3000,6000,12000'
        generate_counter = lambda couter_key, default: Counter(
                [int(i) for i in string.split(common_util.get_config_value_by_key(self.parameters, couter_key, default), ',')]
                )
        self.index_response_counter = generate_counter('index.counter', default_counter_list)
        self.bitrate_response_counter = generate_counter('bitrate.counter', default_counter_list)
    
    def demo(self):
        self.index_response_counter.increment(200)
        print self.index_response_counter.dump()
        print self.logger
        print dir(self.logger)
        print self.logger.level
        print self.logger.name
        self.logger.info('1234')
        self.logger.debug('debug')
           
    
