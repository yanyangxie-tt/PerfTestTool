# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from multiprocessing import Process
from init_script_env import *

def do_load_test(load_test_script, current_process_seq):
    print 'Start process(%s) to do load test' % (current_process_seq)
    try:
        os.system('python %s %s ' % (load_test_script, current_process_seq))
    except Exception, e:
        print e

if __name__ == "__main__":
    config_dict = read_configurations()
    process_number = int(common_util.get_config_value_by_key(config_dict, 'test.execute.process.number', 1))
    load_test_script_file_name = os.path.dirname(os.path.abspath(__file__)) + os.sep + load_test_sigle_process_script_file
    
    process_list = []
    for i in range(process_number):
        p = Process(target=do_load_test, args=(load_test_script_file_name, i,))
        process_list.append(p)

    for p in process_list:
        p.start()
        
        import time
        time.sleep(1)
    
    for p in process_list:
        p.terminate()
