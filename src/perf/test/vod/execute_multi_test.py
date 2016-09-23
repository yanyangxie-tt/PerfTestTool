# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from multiprocessing import Process

from init_script_env import *
from perf.model.configuration import Configurations

class MultipleProcessTest(Configurations):
    def __init__(self, config_file, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        '''
        super(MultipleProcessTest, self).__init__(config_file, **kwargs)
        if not hasattr(self, 'test_execute_process_number'):
            self.process_number = 1
        else:
            self.process_number = int(self.test_execute_process_number)
    
    def run(self):
        process_list = []
        for i in range(self.process_number):
            p = Process(target=self.do_load_test, args=(load_test_script_file_name, i,))
            process_list.append(p)
    
        for p in process_list:
            p.start()
            
            import time
            time.sleep(1)
        
        for p in process_list:
            p.terminate()

    def do_load_test(self, load_test_script, current_process_seq):
        print 'Start process(%s) to do load test' % (current_process_seq)
        try:
            os.system('python %s %s ' % (load_test_script, current_process_seq))
        except Exception, e:
            print e

if __name__ == "__main__":
    multiple_test = MultipleProcessTest(config_file, golden_config_file=golden_config_file)
    multiple_test.run()
