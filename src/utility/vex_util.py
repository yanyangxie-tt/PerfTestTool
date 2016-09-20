# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import re

from utility import time_util

def get_test_result_tmp_dir(result_dir, test_case_name=None):
    if test_case_name is not None:
        result_dir += '-' + test_case_name
    return result_dir

def get_process_result_tmp_dir(result_dir, test_case_name=None, process_number=None, test_prefix='test-result'):
    '''Get result dir for special test case and special process in test machine'''
    r_dir = get_test_result_tmp_dir(result_dir, test_case_name)
    # r_dir += os.sep + test_prefix + '-' + time.strftime("%d-%H-%M-%S", time.localtime())
    r_dir += os.sep + test_prefix
    if process_number is not None:
        r_dir += '-' + str(process_number)
    r_dir += os.sep

    return r_dir

def get_test_content_name_list(content_names, offset=0):
    '''Get test content name list by test_case_content_names in configuration file'''
    p = r'(.*)\[(\d+)~(\d+)\](/*\S*)'  # match test_[1,13]
    test_content_list = []

    for c_name in content_names.split(','):
        t = re.findall(p, c_name)
        if len(t) > 0:
            test_content_list += [t[0][0] + str(i + offset) + t[0][3] for i in range(int(t[0][1]), 1 + int(t[0][2]))]
        else:
            test_content_list.append(c_name)
    return test_content_list

def get_test_client_ip_latest_segment_range(range_string='0~255'):
    p = r'^(\d+)~(\d+)$'  # '0~255'
    rs = re.findall(p, range_string)
    if len(rs) > 0:
        return [i for i in range(int(rs[0][0]), 1 + int(rs[0][1]))]
    else:
        return [i for i in range(0, 256)]

def get_timed_file_name(file_name):
    return '%s-%s' % (file_name, time_util.datetime_2_string(time_util.get_local_now(), "%Y-%m-%d-%H-%M-%S"))
        
def get_datas_in_queue(q):
    if q.empty():
        return None
    
    datas = []
    index = q.qsize()
    while True:
        if q.empty() or index == 0:
            break
        info = str(q.get())
        datas.append(info + '\n')
        index -= 1
    return datas
