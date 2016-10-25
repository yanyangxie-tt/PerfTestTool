#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
Local log analysis script
@author: yanyang.xie@thistech.com
@version: 0.2
@since: 7/14/4013
'''

import datetime
import os
import sys
import traceback

import analysis_util as ay
import common_util as cm
import time_util as tm
import collect_log as cl

here = os.path.dirname(os.path.abspath(__file__))
configs = cm.get_configruations()

vex_componment_type = cm.get_config_value_by_key(configs,'type')
remote_log_dir = cm.get_config_value_by_key(configs,'remote_log_dir')
remote_filtered_log_dir = cm.get_config_value_by_key(configs,'remote_filtered_log_dir')
log_file_name_reg = cm.get_config_value_by_key(configs,'log_file_name_reg')
analysis_start_time_long, analysis_end_time_long = cm.get_analysis_times(configs)

gz_log_file_time_format = cm.get_config_value_by_key(configs,'gz_log_file_time_format')
gz_log_file_time_reg = cm.get_config_value_by_key(configs,'gz_log_file_time_reg')

local_result_dir = cm.get_config_value_by_key(configs,'local_result_dir')

# used for local debug
#remote_log_dir = here
#remote_filtered_log_dir = 'd:/tmp/12345'
#local_result_dir = 'd:/tmp/results'

def do_log_analysis_task():
    try:
        collect_log_file_to_filter_dir()
        analysis_log_file(remote_filtered_log_dir)
    except:
        traceback.print_exc()
        exce_info = 'Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
        print exce_info

# collect logs from remote server and download it to local
def collect_log_file_to_filter_dir():
    print '#'*100
    print 'Execute script to collect logs'
    
    if vex_componment_type is not None and vex_componment_type in ['vex-fe', 'vex-director', 'vex',]:
        log_file_name_reg.replace('vex', vex_componment_type)
    
    print 'Filtered log dir: %s' %(remote_filtered_log_dir)
    print 'Source log dir: %s' %(remote_log_dir)
    print 'Log file reg: %s' %(log_file_name_reg)
    print 'Log analysis start time: %s' %(tm.long_2_datetime(analysis_start_time_long))
    print 'Log analysis end time: %s' %(tm.long_2_datetime(analysis_end_time_long))
    
    #should read parameters and then run collect files
    cl.collect_and_filter_files(remote_filtered_log_dir, remote_log_dir, log_file_name_reg, True, gz_log_file_time_reg, analysis_start_time_long, analysis_end_time_long, gz_log_file_time_format)
    
# analysis log files in local
def analysis_log_file(filtered_log_dir):
    global local_result_dir
    if local_result_dir is None:
        local_result_dir = here
    
    file_list = []
    for t_file in os.listdir(filtered_log_dir):
        if t_file.split('.', 1)[1] == 'gz':
            continue
        else:
            file_list.append(filtered_log_dir + os.sep + t_file)
    
    # get log analysis time
    start_time_long, end_time_long = cm.get_analysis_times(configs)
    
    # init local result dir
    today = tm.datetime_2_string(datetime.datetime.utcnow(), t_format='%Y-%m-%d')
    ay.analysis_log_files(file_list, local_result_dir + os.sep + 'results', 'analysis-result-%s.txt' %(today), 'analysis-result-%s.xls' %(today), start_time_long, end_time_long)

def init_local_tmp_dir():
    local_log_dir = cm.get_config_value_by_key(configs, 'local_log_dir')
    if not os.path.exists(local_log_dir):
        os.makedirs(local_log_dir)

if __name__ == '__main__':
    init_local_tmp_dir()
    do_log_analysis_task()
