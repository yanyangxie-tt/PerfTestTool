# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com

import os
import string
import sys

sys.path.append(os.path.join(os.path.split(os.path.realpath(__file__))[0], "../.."))
from utility import common_util
from utility.mysql_connecter import MySQLConnection

class Configurations(object):
    '''
    Read configurations, convert configured parameters to object attribute with right format.
    If golden_config_file exists in kwargs, parameter in it will instead the same in config file.
    '''
    def __init__(self, config_file, **kwargs):
        '''
        Initialized configuration and logs with a properties file and log file
        @param golden_config_file: will replace parameters in config file
        '''
        self.config_file = config_file
        
        self.list_sep = ','
        self.config_sep = '.'
        
        if not os.path.exists(self.config_file) or not os.path.isfile(self.config_file):
            raise Exception('Configuration file %s do not exist' % (self.config_file))
            sys.exit(1)
            
        self.parameters = {}
        self.parameters.update(kwargs)
        
        self.update_default_config()
        self.update_golden_config()
        self.update_config_in_db()
        
        self.init_configured_parameters()
        self.init_configured_parameters_default_value()
    
    def update_config(self):
        self.update_config_in_db()
        self.init_configured_parameters()
        self.update_config_individual_step()
    
    def update_config_individual_step(self):
        pass
    
    def update_default_config(self):
        self.parameters.update(common_util.load_properties(self.config_file,))

    def update_golden_config(self):
        if self.parameters.has_key('golden_config_file'):
            golden_config_file = self.parameters.get('golden_config_file')
            if os.path.exists(golden_config_file) and os.path.isfile(golden_config_file):
                self.parameters.update(common_util.load_properties(golden_config_file))

    def update_config_in_db(self):
        if not hasattr(self, 'connector'):
            self.connector = self.get_db_connection()
        self.parameters.update(self.get_configured_parameters_in_db())
    
    def init_configured_parameters(self):
        ''' Read configured parameters and then set general parameters as object attribute '''
        for p_key, p_value in self.parameters.items():
            key = p_key.replace(self.config_sep, '_')
                
            if p_value.find(self.list_sep) > 0:
                p_value = [self._transform_numeric_type(value)  for value in string.split(p_value, self.list_sep)]
            elif p_value and string.lower(p_value) == 'true':
                p_value = True
            elif p_value and string.lower(p_value) == 'false':
                p_value = False
            else:
                p_value = self._transform_numeric_type(p_value)

            setattr(self, key, p_value)
    
    def get_db_connection(self):
        db_required = ['db.host', 'db.user', 'db.password', 'db.database']
        
        for p in db_required:
            if not self.parameters.has_key(p):
                print 'Not configured required db parameters %s' %(p)
                return None
        
        try:
            user = common_util.get_config_value_by_key(self.parameters, 'db.user')
            host = common_util.get_config_value_by_key(self.parameters, 'db.host')
            password = common_util.get_config_value_by_key(self.parameters, 'db.password')
            database = common_util.get_config_value_by_key(self.parameters, 'db.database')
            port = int(common_util.get_config_value_by_key(self.parameters, 'db.port'))
            
            connector = MySQLConnection(host, user, password, database, port=port)
            return connector
        except Exception,e:
            print e
            return None
    
    def get_configured_parameters_in_db(self):
        if self.connector is None:
            return {}
        
        try:
            use_vex_config_in_db = common_util.get_config_value_by_key(self.parameters, 'db.vex.config.enable', 'False')
            vex_config_table_name = common_util.get_config_value_by_key(self.parameters, 'db.vex.config.table', None)
            if string.lower(use_vex_config_in_db) != 'true' or vex_config_table_name is None:
                return {}
            
            #project_name = common_util.get_config_value_by_key(self.parameters, 'project.name')
            test_case_type = common_util.get_config_value_by_key(self.parameters, 'test.case.type')
            
            #self.connector.execute('select * from %s where project_name="%s" and test_case_type="%s"' %(vex_config_table_name, project_name, test_case_type))
            #print 'select * from %s where test_type="%s"' %(vex_config_table_name, test_case_type)
            self.connector.execute('select * from %s where test_type="%s"' %(vex_config_table_name, test_case_type))
            result = self.connector.find_one()
            if result is not None:
                test_config = result['test_config']
                project_name = result['project_name']
                content_size = int(result['content_size'])
                bitrate_number = result['bitrate_number']
                session_number = result['session_number']
                warm_up_minute = result['warm_up_minute']
                content_prefix = result['content_prefix']
                
                if content_size <=1:
                    content_names = content_prefix + "1"
                else:
                    content_names = '%s[1~%s]' %(content_prefix, str(content_size))
                
                config_dict_in_db = {
                    'project.name': str(project_name),
                    'test.bitrate.request.number':str(bitrate_number),
                    'test.case.concurrent.number':str(session_number),
                    'test.case.client.number':str(session_number),
                    'test.case.warmup.period.minute':str(warm_up_minute),
                    'test.case.content.names':str(content_names),
                    }
                
                try:
                    if test_config.strip() != "":
                        config_dict_in_db.update(eval(test_config.strip())) 
                except Exception, e:
                    print 'Failed to parse test_config. please make sure its dict format. %s' %(e)
                return config_dict_in_db
        except Exception, e:
            print 'Failed to read configuration from DB. %s' %(e)
            return {}
    
    def init_configured_parameters_default_value(self):
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

if __name__ == '__main__':
    config_file = '/Users/xieyanyang/work/learning/PerfTest/src/perf/test/linear/config.properties'
    golden_config_file = '/Users/xieyanyang/work/learning/PerfTest/src/perf/test/linear/config-golden.properties'
    c = Configurations(config_file, golden_config_file=golden_config_file)