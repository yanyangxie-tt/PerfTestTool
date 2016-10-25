#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
@author: yanyang.xie@thistech.com
@version: 0.3
@since: 07/14/2013
'''
import os
import re
import string

import xlwt

import time_util as tm
import common_util as cm
import ignore_rules as irules
import merge_rules as mrules

time_format = '%Y%m%d %H:%M:%S'

# vex error log format
log_date_reg = r'^[0-9]{8}'  # vex error log will be started by digit(8 digit number)
log_time_reg = r'([0-9]{8}\s+[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}).*'  # time regular expression of vex error log
log_seperate_reg = r'\[.*\]'  # vex error log is seperated by [any character]

# error log group info
log_error_group_minute=cm.get_log_analysis_group_minute()

# Merge similar errors and ignore special errors
merge_rule_list = mrules.vex_merge_rule_list + mrules.vex_fe_merge_rule_list + mrules.vex_director_merge_rule_list
ignore_rule_list = irules.vex_ignore_rule_list + irules.vex_fe_ignore_rule_list + irules.vex_director_ignore_rule_list

'''
analysis log files and export results
@param log_file_path_list: log file list
@param analysis_result_dir: dir of exported result
@param result_file_name_txt: result file. txt format
@param result_file_name_xml: result file. xml format
@param start_time_long: log analysis start time
@param start_time_long: log analysis end time
@param log_error_group_minute: group errors in log_error_group_minute minutes for xml file
@param ignore_rule_list: error line in logs which is matched special ignore rule in ignore_rule_list will be ignored
@param merge_rule_list: error line in logs which is matched special rule in merge_rule_list will be consider same error
'''
def analysis_log_files(log_file_path_list, analysis_result_dir, result_file_name_txt, result_file_name_xml=None, start_time_long=None, end_time_long=None, log_error_group_minute=log_error_group_minute, ignore_rule_list=ignore_rule_list, merge_rule_list=merge_rule_list):
    total_error_dict = generate_total_error_dict(log_file_path_list, start_time_long, end_time_long,ignore_rule_list, merge_rule_list)
    error_report = generate_error_report_list(total_error_dict)
    print 'Export vex error analysis data into local file %s' % (analysis_result_dir + os.sep + result_file_name_txt)
    cm.write_to_file(error_report, analysis_result_dir, result_file_name_txt, 'w', True)
    
    if start_time_long is not None and end_time_long is not None and result_file_name_xml is not None:
        error_list = get_sorted_error_list(total_error_dict)
        error_group_time_dict = group_errors_by_timestamps(total_error_dict,start_time_long, end_time_long, log_error_group_minute)
        print 'Export vex error analysis data in xml format into local file %s' % (analysis_result_dir + os.sep + result_file_name_xml)
        
        vex_componment_type = cm.get_config_value_by_key(cm.get_configruations(), 'type')
        write_to_excel(error_group_time_dict, error_list, analysis_result_dir, result_file_name_xml, tag=vex_componment_type)

'''
Generate total error information dict using all the error file
@param log_file_path_list: error file list
@param start_time_long: log analysis start time
@param start_time_long: log analysis end time
@param ignore_rule_list: error line in logs which is matched special ignore rule in ignore_rule_list will be ignored
@param merge_rule_list: error line in logs which is matched special rule in merge_rule_list will be consider same error
'''
def generate_total_error_dict_old(log_file_path_list, start_time_long=None, end_time_long=None, ignore_rule_list=None, merge_rule_list=None):
    total_error_dict = {}
    for log_file_path in log_file_path_list:
        error_dict = generate_error_info_dict_by_error_file(log_file_path, start_time_long, end_time_long, ignore_rule_list, merge_rule_list)
        for key in error_dict:
            if not total_error_dict.has_key(key):
                total_error_dict[key] = []
            total_error_dict[key] += error_dict[key]
    return total_error_dict

def generate_total_error_dict(log_file_path_list, start_time_long=None, end_time_long=None, ignore_rule_list=None, merge_rule_list=None):
    parameter_list = [(t_file, start_time_long, end_time_long, ignore_rule_list, merge_rule_list) for t_file in log_file_path_list]
    
    from multiprocessing import Pool
    pool = Pool(8)
    
    work_list = []
    for parameter in parameter_list:
        worker = pool.apply_async(generate_error_info_dict_by_error_file, parameter)
        work_list.append(worker)
    
    error_result_list = [w.get() for w in work_list]
    total_error_dict = {}
    for error_dict in error_result_list:
        for key in error_dict:
            if not total_error_dict.has_key(key):
                total_error_dict[key] = []
            total_error_dict[key] += error_dict[key]
    return total_error_dict

'''
Generate error information dict for one error file
@param log_file_path: the absolute path of log file

@return: error information dict
@attention: error information dict format: [error_message:[datetime1, datetime2,]]
'''
def generate_error_info_dict_by_error_file(log_file_path, start_time_long=None, end_time_long=None, ignore_rule_list=None, merge_rule_list=None):
    error_dict = {}
    
    pf = open(log_file_path, 'rU')
    for line in pf:
        if string.strip(line) == '' or string.strip(line) == '\n':
            continue
        
        # if the line has special string which is in ignore rule list, should be ignored.
        if cm.is_ignore(line, ignore_rule_list):
            continue
        
        # if the line is not started with 8 digit number, then it is a detail exception info, not summary.
        if len(cm.matched_string(line, log_date_reg)) == 0:
            continue
        
        # if the log time is less than the log_start_time which we want to analysis, ignore it
        log_time = tm.string_2_long(cm.matched_string(line, log_time_reg)[0], time_format)
        if start_time_long is not None and log_time < start_time_long:
            continue
        
        if start_time_long is not None and log_time > end_time_long:
            continue
        
        # replace the sub string to '' follwing the ignore rule
        line = line.strip('\n').strip()
        if merge_rule_list is not None:
            for merge_rule in merge_rule_list:
                line = cm.replace_string(line, merge_rule, '')
        
        # start to split the line of error info
        split_list = cm.split_string(line, log_seperate_reg)
        if len(split_list) > 0 :
            # The latest info in the split list is the real error info, count its number 
            error_info = split_list[-1]
            if not error_dict.has_key(error_info):
                error_dict[error_info] = []
            error_dict[error_info].append(tm.long_2_datetime(log_time))
    return error_dict

'''
Write errors into excel file.
'''
def write_to_excel(total_error_time_group_dict, total_error_list, out_file_dir, out_file_name, is_delete=True, tag=None):
    if not os.path.exists(out_file_dir):
        os.makedirs(out_file_dir)

    try:
        if not out_file_dir[-1] == os.sep:
            out_file_dir += os.sep
        
        if is_delete and os.path.exists(out_file_dir + out_file_name):
            os.remove(out_file_dir + out_file_name)
            
        # write to excel
        x_file = xlwt.Workbook()
    
        # write filtered monitor info
        sheet_name = tag + '_analysis_result' if tag is not None else 'analysis_result'
        total_content_sheet = x_file.add_sheet(sheet_name)
        
        all_time_list = total_error_time_group_dict.keys()
        all_time_list.sort()
        # write title
        for i in range(len(total_error_list)):
            if i > 250:  # Execl column limit is 255
                    break
            total_content_sheet.write(0, i + 1, total_error_list[i])
        
        # write time stamps
        for i in range(len(all_time_list)):
            total_content_sheet.write(i + 1, 0, all_time_list[i]) 
        
        for i in range(len(all_time_list)):
            error_dict_in_special_time = total_error_time_group_dict[all_time_list[i]]
            for j in range(len(total_error_list)):
                if j > 250:  # Execl column limit is 255
                    break
                special_error = total_error_list[j]
                if error_dict_in_special_time.has_key(special_error):
                    total_content_sheet.write(i + 1, j + 1, float(error_dict_in_special_time[special_error]))
                else:
                    total_content_sheet.write(i + 1, j + 1, float(0))
        
        # save excel into local
        x_file.save(out_file_dir + out_file_name)
        
    except IOError as err:
        print('Open local file %s error: {0}'.format(err) % (out_file_dir + out_file_name))
    
'''
Init a error dict for the final statistics
@return: dict
@attention: dict format is {datetime1:{}, datetime2:{},}
'''
def init_time_group(start_time_long, end_time_long,log_error_group_minute=5):
    start_time = tm.get_closer_time_in_minute(tm.long_2_datetime(start_time_long), log_error_group_minute)
    end_time = tm.get_closer_time_in_minute(tm.long_2_datetime(end_time_long), log_error_group_minute)
    
    time_point_list = tm.get_time_point_list(tm.datetime_2_long(start_time), tm.datetime_2_long(end_time), log_error_group_minute, time_format)
    
    group_dict = {}
    for t in time_point_list:
        group_dict[t] = {}
    
    return group_dict

'''
Converted and group errors by special time window.
@param total_error_dict: all the errors which format is {error_message:[datetime1, datetime2,], error_message:[datetime2,],}
@return: Converted error dict which format is {datetime1:{error_message:error_count,}, datetime2:{},}
'''
def group_errors_by_timestamps(total_error_dict, start_time_long, end_time_long, log_error_group_minute=5):
    error_group_time_map = init_time_group(start_time_long, end_time_long, log_error_group_minute)
    
    for key in total_error_dict.keys():
        error_time_list = total_error_dict[key]
        for error_datetime in error_time_list:
            error_time_string = tm.datetime_2_string(tm.get_closer_time_in_minute(error_datetime, log_error_group_minute), time_format)
            
            if not error_group_time_map[error_time_string].has_key(key):
                error_group_time_map[error_time_string][key] = 0
            error_group_time_map[error_time_string][key] += 1
    
    return error_group_time_map

'''
Get error list from total error. Specally the list will be sorted by the count of error.
@return: sorted error list
@attention: total dict format is {error_message:[datetime1, datetime2,], error_message:[datetime1,],}
'''
def get_sorted_error_list(total_error_dict):
    sorted_error_list = []
    reverse_dict = {}
    for error_message in total_error_dict.keys():
        time_stamp_list_size = len(total_error_dict[error_message])
        if not reverse_dict.has_key(time_stamp_list_size):
            reverse_dict[time_stamp_list_size] = []
        reverse_dict[time_stamp_list_size].append(error_message)
    
    reverse_dict_keys = reverse_dict.keys()
    reverse_dict_keys.sort()
    reverse_dict_keys.reverse()
    for key in reverse_dict_keys:
        for error_message in reverse_dict.get(key):
            sorted_error_list.append(error_message)
    return sorted_error_list

'''
Generate error informations
@param error_dict: error information dict
@param max_value_export_major_error: Max value of exported major errors

@return: error report line list
'''
def generate_error_report_list(error_dict, max_value_export_major_error=10):
    error_message_list = get_sorted_error_list(error_dict)
    lines = []
    
    # generate total error messages
    lines.append('*' * 80 + '\n')
    lines.append('Total warning and error messages:\n')
    
    for key in error_message_list:
        #print 'ERROR: %s \n  %s' % (key, error_dict[key])
        lines.append(str(len(error_dict[key])) + '\ttimes:\t' + key + '\t\n')
    lines.append('\n')
    
    # generate major error
    lines.append('*' * 80 + '\n')
    lines.append('Major warning and error messages and timestamps:\n')
    
    major_error_message_list = error_message_list
    if len(error_message_list) > max_value_export_major_error:
        major_error_message_list = error_message_list[0:max_value_export_major_error]
        
    for error_message in major_error_message_list:
        lines.append('ERROR: %s ' % (error_message))
        error_timestamp_list = list(set(error_dict[error_message]))
        error_timestamp_list.sort()
        i = 0
        tmp_string = ''
        for error_datetime in error_timestamp_list:
            tmp_string += tm.datetime_2_string(error_datetime, time_format) + ','
            i += 1
            if i > 200:
                break
        lines.append('\n\tTimestamp: %s \n' % (tmp_string))
    
    return lines

'''
Filter error file list by analysis time window
@param file_list: original file list
@param start_time_long: start time of log analysis
@param end_time_long: end time of log analysis
@param log_rorate_time_format: time format for log rotate
@param log_rotate_date_reg: time regular expression for log rotate
@return: filtered file list
# log file rorate time format, such as vex_error.log-2014-06-16.gz
'''
def filter_error_file_by_time(file_list, start_time_long, end_time_long, log_rorate_time_format='%Y-%m-%d', log_rotate_date_reg='[0-9]{4}-[0-9]{2}-[0-9]{2}'):
    start_time_date = tm.long_2_datetime(start_time_long)
    end_time_date = tm.long_2_datetime(end_time_long)

    start_time_long = tm.datetime_2_long(tm.get_today(start_time_date))
    end_time_long = tm.datetime_2_long(tm.get_today(end_time_date))
    
    tmp_list = file_list
    for t_file in file_list:
        if t_file.find('.gz') < 1:
            continue
        
        m_list = re.findall(log_rotate_date_reg, t_file)
        if m_list is None or len(m_list)==0:
            continue
        
        log_file_time_long = tm.string_2_long(m_list[0], log_rorate_time_format)
        if log_file_time_long < start_time_long or log_file_time_long > end_time_long:
            tmp_list.remove(t_file)
    return tmp_list