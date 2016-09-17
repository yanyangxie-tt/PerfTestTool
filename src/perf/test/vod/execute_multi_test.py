#!/usr/bin/python
# -*- coding=utf-8 -*-

from multiprocessing import Process
import os
import sys
import time

sys.path.append(os.path.join(os.path.split(os.path.realpath(__file__))[0], "../../.."))
from utility import common_util

load_test_sub_folder = sys.argv[1] if len(sys.argv) > 1 else ''
load_test_script_file_name = sys.argv[2] if len(sys.argv) > 2 else 'vod_perf_test.py' 

def do_load_test(remote_script_tmp_dir, load_test_script, current_process_seq):
    print 'Start process(%s) to do load test' % (current_process_seq)
    os.chdir(remote_script_tmp_dir)
    os.system('python %s%s %s ' % (remote_script_tmp_dir, load_test_script, current_process_seq))

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    remote_script_tmp_dir = sys.argv[1] if len(sys.argv) > 1 else here + os.sep
    
    config_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + '%s/config.properties' % (load_test_sub_folder)
    config_golden_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + '%s/config-golden.properties' % (load_test_sub_folder)
    
    config_dict = common_util.load_properties(config_file)
    config_dict.update(common_util.load_properties(config_golden_file))
    
    if config_dict is None or len(config_dict) == 0:
        print 'Not found any configurations using file %s' % (os.path.dirname(os.path.abspath(__file__)) + os.sep + 'config.properties')
        sys.exit(1)
    
    process_number = int(config_dict['test.execute.process.number']) if config_dict.has_key('test.execute.process.number') else 1
    
    process_list = []
    for i in range(process_number):
        p = Process(target=do_load_test, args=(remote_script_tmp_dir, load_test_script_file_name, i,))
        process_list.append(p)

    for p in process_list:
        p.start()
        time.sleep(1)
    
    for p in process_list:
        p.terminate()
