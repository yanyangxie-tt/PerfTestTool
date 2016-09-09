##############################################################################################################################
import os
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
