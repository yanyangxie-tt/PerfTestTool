import os
import threading
import time

from Crypto.Util import number

from perf.test.model.task import VEXScheduleReqeustsTask
from perf.test.model.vex_perf_test import VEXPerfTestBase


class VODPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, log_file, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VODPerfTest, self).__init__(config_file, log_file, **kwargs)
        self.init_environment()
    
    def generate_requests(self):
        pass
    
    def add_task(self):
        while True:
            if self.task_queue.full():
                print 'full, sleep(3)'
                time.sleep(3)
                continue
            
            task = VEXScheduleReqeustsTask('http://www.baidu.com', '192.168.1.1', 'zone1', 'location1')
            self.task_queue.put_nowait(task)
    
    def prepare_task(self):
        self.task_generater = threading.Thread(target=self.add_task)
        self.task_generater.setDaemon(True)
        self.task_generater.start()
        
    def run(self):
        self.prepare_task()
        print 'do others'
        time.sleep(1000)
        print '#' * 100
        print 'done'
    

if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    
    config_file = here + os.sep + 'config.properties'
    log_file = here + os.sep + 'vex.log'
    golden_config_file = here + os.sep + 'config-golden.properties'
    
    v = VODPerfTest(config_file, log_file, golden_config_file=golden_config_file)
    v.run()
