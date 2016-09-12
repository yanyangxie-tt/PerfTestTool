##############################################################################################################################
import os
import re
import time


def get_process_result_tmp_dir(result_dir, test_case_name=None, process_number=None, test_prefix='test-result-'):
    '''Get result dir for special test case and special process in test machine'''
    r_dir = result_dir
    if test_case_name is not None:
        r_dir += '-' + test_case_name
    
    r_dir += os.sep + test_prefix + time.strftime("%d-%H-%M-%S", time.localtime())
    if process_number is not None:
        r_dir += '-' + str(process_number)
    r_dir += os.sep

    return r_dir

def get_test_content_name_list(content_names, offset=0):
    '''Get test content name list by test_content_names in configuration file'''
    p = r'(.*)\[(\d+)~(\d+)\](/*\S*)'  # match test_[1,13]
    test_content_list = []

    for c_name in content_names.split(','):
        t = re.findall(p, c_name)
        if len(t) > 0:
            test_content_list += [t[0][0] + str(i + offset) + t[0][3] for i in range(int(t[0][1]), 1 + int(t[0][2]))]
        else:
            test_content_list.append(c_name)
    return test_content_list  
