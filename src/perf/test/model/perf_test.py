# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import logging
import os
import string
import sys

sys.path.append(os.path.join(os.path.split(os.path.realpath(__file__))[0], "../.."))
from utility import common_util, logger_util

class PerfTestBase(object):
    '''Basic module for performance test'''
    def __init__(self, config_file, log_file=None, log_level='DEBUG', **kwargs):
        '''Initialized configuration and logs with a properties file and log file
        @param golden_config_file: will replace parameters in config file
        
        '''
        self.config_file = config_file
        
        self.list_sep = ','
        self.config_sep = '.'
        
        if not os.path.exists(self.config_file) or not os.path.isfile(self.config_file):
            raise Exception('Configuration file %s do not exist' % (self.config_file))
            sys.exit(1)
            
        self.parameters = common_util.load_properties(self.config_file)
        self.parameters.update(kwargs)
        
        if kwargs.has_key('golden_config_file'):
            golden_config_file = kwargs.get('golden_config_file')
            if os.path.exists(golden_config_file) and os.path.isfile(golden_config_file):
                self.parameters.update(common_util.load_properties(golden_config_file))
        
        if self.parameters.has_key('log.level'):
            self.log_level = self.parameters.get('log.level')
        
        self.init_configred_parameters()
        self.init_configred_parameters_default_value()

    def init_log(self, log_file, log_level, log_name=None):
        logger_util.setup_logger(log_file, name=log_name, log_level=log_level)
        self.logger = logging.getLogger(name=log_name)
    
    def init_configred_parameters(self):
        ''' Read configured parameters and then set general parameters as object attribute '''
        for p_key, p_value in self.parameters.items():
            key = p_key.replace(self.config_sep, '_')
                
            if p_value.find(self.list_sep) > 0:
                p_value = [self._transform_numeric_type(value)  for value in string.split(p_value, self.list_sep)]
            elif p_value and string.lower(p_value) == 'true':
                p_value = True
            else:
                p_value = self._transform_numeric_type(p_value)

            setattr(self, key, p_value)
    
    def init_configred_parameters_default_value(self):
        # initial your parameters which is required a default value using self._set_attr()
        pass
    
    def _transform_numeric_type(self, value):
        try:
            return int(value)
        except:
            return value

    def _has_attr(self, attr_name):
        if not hasattr(self, attr_name):
            return False
        else:
            return getattr(self, attr_name, None)

    def _set_attr(self, attr_name, attr_value, update=False):
        if self._has_attr(attr_name):
            if update:
                setattr(self, attr_name, attr_value)
        else:
            setattr(self, attr_name, attr_value)
