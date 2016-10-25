#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
@author: yanyang.xie@thistech.com
@version: 0.2
@since: 06/24/2013
'''
import re

import time_util as tm
import common_util as cm

'''
Collect files
@param dest_dir: all the expected logs will be put into dest file dir
@param src_dir: source file directory
@param src_file_name_reg: use file regular expression to filter files
@param is_recur: whether to collect file in recursive sub folder
@param gz_file_time_reg: get time string from gz file name using gz_file_time_reg. If set, will use start and end time to filter file 
@param gz_file_start_time_long: filter gz file by start time
@param gz_file_end_time_long: filter gz file by end time
@param gz_file_time_format: gz file time format, default is %Y-%m-%d.
'''
def collect_and_filter_files(dest_dir, src_dir, src_file_name_reg, is_recur=True, gz_file_time_reg=None, analysis_start_time_long=None, analysis_end_time_long=None, gz_file_time_format='%Y-%m-%d'):
    log_file_path_list = cm.get_matched_file_list(src_dir, src_file_name_reg)
    if gz_file_time_reg is not None:
        log_file_path_list = filter_gz_file_by_time(log_file_path_list, gz_file_time_reg, analysis_start_time_long, analysis_end_time_long,gz_file_time_format)
    cm.copy_file_2_dest(log_file_path_list, dest_dir)

'''
Filter error file list by analysis time window
@param file_list: original file list
@param start_time_long: start time of log analysis
@param end_time_long: end time of log analysis
@param gz_file_time_format: time format for log rotate

@return: filtered file list
'''
def filter_gz_file_by_time(file_list, gz_file_time_reg, start_time_long=None, end_time_long=None, gz_file_time_format='%Y-%m-%d'):
    # get 00:00:00 of start day and end day
    if start_time_long is not None:
        start_time_date = tm.long_2_datetime(start_time_long)
        start_time_long = tm.datetime_2_long(tm.get_today(start_time_date))
    
    if end_time_long is not None:
        end_time_date = tm.long_2_datetime(end_time_long)
        end_time_long = tm.datetime_2_long(tm.get_today(end_time_date))
    
    tmp_list = file_list[:]
    for t_file in file_list:
        if t_file.find('.gz') < 1:
            continue
        
        m_list = re.findall(gz_file_time_reg, t_file)
        if m_list is None or len(m_list)==0:
            continue
        
        log_file_time_long = tm.string_2_long(m_list[0], gz_file_time_format)
        if start_time_long is not None and log_file_time_long < start_time_long:
            tmp_list.remove(t_file)
            continue
        
        if end_time_long is not None and log_file_time_long > end_time_long:
            tmp_list.remove(t_file)
    return tmp_list

if __name__ == '__main__':
    print '#'*100
    print 'Start to collect log files'
    config_dict = cm.get_configruations()
    remote_log_dir = cm.get_config_value_by_key(config_dict,'remote_log_dir')
    remote_filtered_log_dir = cm.get_config_value_by_key(config_dict,'remote_filtered_log_dir')
    log_file_name_reg = cm.get_config_value_by_key(config_dict,'log_file_name_reg')
    #vex_componment_type = cm.get_config_value_by_key(config_dict,'type')
    
    print 'log file name reg: %s' %(log_file_name_reg)
    print 'vex componment type: %s' %(vex_componment_type)
    #if vex_componment_type is not None and vex_componment_type in ['vex-fe', 'vex-director', 'vex',]:
    #    log_file_name_reg = log_file_name_reg.replace('vex', vex_componment_type)
    print 'log file name reg: %s' %(log_file_name_reg)
    
    print 'Filtered log dir: %s' %(remote_filtered_log_dir)
    print 'Source log dir: %s' %(remote_log_dir)
    print 'Log file reg: %s' %(log_file_name_reg)
    
    gz_log_file_time_format = cm.get_config_value_by_key(config_dict,'gz_log_file_time_format')
    gz_log_file_time_reg = cm.get_config_value_by_key(config_dict,'gz_log_file_time_reg')
    
    analysis_start_time_long, analysis_end_time_long = cm.get_analysis_times(config_dict)
    print 'Log analysis start time: %s' %(tm.long_2_datetime(analysis_start_time_long))
    print 'Log analysis end time: %s' %(tm.long_2_datetime(analysis_end_time_long))
    
    #should read parameters and then run collect files
    collect_and_filter_files(remote_filtered_log_dir, remote_log_dir, log_file_name_reg, True, gz_log_file_time_reg, analysis_start_time_long, analysis_end_time_long, gz_log_file_time_format)


