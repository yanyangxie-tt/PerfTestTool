'''
Created on 2014-7-10

@author: yanyang
'''
import os
import re
import shutil
import string
import time

import time_util as tm


configs = None

# load properties to dict
def load_properties(file_dir, file_name):
    infos = {}
    config_file = file_dir + os.path.sep + file_name
    if not os.path.exists(config_file):
        return {}
    
    pf = open(config_file, 'rU')
    for line in pf:
        if string.strip(line) == '' or string.strip(line) == '\n' or string.find(line, '#') == 0:
            continue
        line = string.replace(line, '\n', '')
        tmp = line.split("=", 1)
        values = tmp[1].split("#", 1)
        
        infos[string.strip(tmp[0])] = string.strip(values[0])
    pf.close()
    return infos

# get configuration dict
def get_configruations(config_file='config.properties'):
    global configs
    if configs is None:
        print 'Load basic configurations from %s' % (config_file)
        configs = load_properties(os.path.dirname(os.path.abspath(__file__)), config_file)
    return configs

# get configured value by key from configuration value
def get_config_value_by_key(config_dict, key):
    return string.strip(config_dict[key]) if config_dict.has_key(key) and config_dict[key] != '' else None

# get log naalysis group minute
def get_log_analysis_group_minute():
    group_minute = get_config_value_by_key(get_configruations(),'log_analysis_group_minute')
    if group_minute is None:
        group_minute = 5
    return int(group_minute)

'''
Split the source string by the occurrences of the pattern
@param t_string: origin string
@param reg: regular expression

@return: a list containing the resulting substrings.
'''
def split_string(t_string, reg):
    p = re.compile(reg)
    return p.split(t_string)

'''
Find all the matched string by the occurrences of the pattern
@param t_string: origin string
@param reg: regular expression

@return: a list of all non-overlapping matches in the string
'''
def matched_string(t_string, reg):
    return re.findall(reg, t_string)

'''
Whether a error message should be ignore.
'''
def is_ignore(error_message, ignore_rule_list):
    if ignore_rule_list is None:
        return False
    
    s_ignore = False
    for ignore_rule in ignore_rule_list:
        if error_message.find(ignore_rule) > -1:
            s_ignore = True
            break
    return s_ignore

'''
replace old sub string which is matched the regular expression to new substring
@param t_string: origin string
@param req: regular expression
@param new_sub: new substring
'''
def replace_string(t_string, reg, new_sub=''):
    matched_list = matched_string(t_string, reg)
    if len(matched_list) > 0:
        for old_sub in matched_list:
            if isinstance(old_sub, tuple):
                for segment in old_sub:
                    t_string = string.replace(t_string, segment, '')
            else:
                t_string = string.replace(t_string, old_sub, '')
    
    return t_string

'''
get matched file list in special dir
@param file_dir: file dir
@param file_name_reg: file name regular expression
@param recur: whether to find in sub folder

@return: file list
'''
def get_matched_file_list(file_dir, file_name_reg, recur=True):
    file_list = []
    for root, dirs, files in os.walk(file_dir, recur):
        print root, dirs, files
        for t_file in files:
            t =  re.match(file_name_reg, str(t_file))
            if t:
                file_list.append(root + os.sep + t_file)
    return file_list

'''
# copy file list into dest directroy
@param src_file_list: source file list
@param dest_dir: dest directory
'''
def copy_file_2_dest(src_file_list, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
        time.sleep(2)
    os.makedirs(dest_dir)
    
    if dest_dir[-1] != os.sep:
        dest_dir += os.sep
    
    for src_file in src_file_list:
        src_file_name = string.split(src_file, os.sep)[-1]
        shutil.copyfile(src_file, dest_dir + src_file_name)

'''
get all files in one dir
'''
def get_all_files_in_dir(f_dir, gunzip=True):
    if not f_dir[-1] == os.sep:
        f_dir += os.sep
    
    if gunzip:
        os.chdir(f_dir)
        files = os.listdir(f_dir)
        for t_file in files:
            try:
                if t_file.find('.gz') > 0 and t_file.find('.gz') == len(t_file) -3:
                    os.popen('gunzip -f %s' %(t_file))
            except:
                print 'unzip file %s failed.' %(t_file)
    
    file_path_list = []
    files = os.listdir(f_dir)
    for t_file in files:   
        file_path_list.append(f_dir + t_file)
    
    return file_path_list

'''
Write lines into file
@param lines: informations
@param out_file_dir: out file directory 
@param out_file_name: out file name
@param mode: write file mode, 'w' or 'a'
@param is_delete: whether delete exist file with same name before write new file
'''
def write_to_file(lines, out_file_dir, out_file_name, mode='a', is_delete=True):
    if not os.path.exists(out_file_dir):
        os.makedirs(out_file_dir)

    try:
        if not out_file_dir[-1] == os.sep:
            out_file_dir += os.sep
        
        if is_delete and os.path.exists(out_file_dir + out_file_name):
            print 'remove older file %s' %(out_file_dir + out_file_name)
            os.remove(out_file_dir + out_file_name)
        output = open(out_file_dir + out_file_name, mode)
        output.writelines(lines)
    except IOError as err:
        print('Open local file %s error: {0}'.format(err) % (out_file_dir + out_file_name))
    finally:
        output.close()

# get log analysis start time and end time
def get_analysis_times(config_dict):
    log_analysis_time_format = config_dict.get('log_analysis_time_format')
    log_analysis_start_time = config_dict.get('log_analysis_start_time')
    log_analysis_end_time = config_dict.get('log_analysis_end_time')
    log_analysis_time_window_before_end = config_dict.get('log_analysis_time_window_before_end')
    if log_analysis_end_time is None or log_analysis_end_time == '':
        analysis_end_time_long = tm.datetime_2_long(tm.get_datetime_before(delta_hours=0))
    else:
        analysis_end_time_long = tm.string_2_long(log_analysis_end_time, log_analysis_time_format)
        
    if log_analysis_time_window_before_end is not None and log_analysis_time_window_before_end != '':
        analysis_start_time_long = tm.datetime_2_long(tm.get_datetime_before(tm.long_2_datetime(analysis_end_time_long), delta_hours=int(log_analysis_time_window_before_end)))
    elif log_analysis_start_time is not None and log_analysis_start_time != '':
        analysis_start_time_long = tm.string_2_long(log_analysis_start_time, log_analysis_time_format)
    else:
        analysis_start_time_long = None
        
    # print tm.long_2_string(analysis_start_time_long), tm.long_2_string(analysis_end_time_long)
    return analysis_start_time_long, analysis_end_time_long

'''
if __name__ == '__main__1': 
    reg=r'\[.*\]'
    str1 = '20131210 03:42:27.153 ERROR [vex] [vep-156] [c.t.v.u.RemoteAdsProcessingUtil.getAdsResponse:79] Failed to get a'
    print split_string(str1,reg)
    print matched_string(str1,reg)

if __name__ == '__main__3':   
    str1 = '123456789 aaaaa'
    str2 = 'aaa'
    reg = r'^[0-9]{8}'
    print matched_string(str1,reg)
    print matched_string(str2,reg)
    
    reg2 = r'/\d{4}-\[01]\d-[0123]\d\s{1,2}[012]\d:[0-6]\d/'
    reg2 = r'([0-9]{8}\s+[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}).*'
    str4 = '20100911 19:48:29. 12345'
    print  matched_string(str4, reg2)
    
    str3 = '20131210 03:42:27.153 ERROR [vex] [vep-156] [c.t.v.u.RemoteAdsProcessingUtil.getAdsResponse:79] Failed t'
    log_time_reg = r'([0-9]{8}\s+[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}).*'
    print matched_string(str3,log_time_reg)

if __name__ == '__main__4':
    str1='Failed to get uri: http://172.31.13.238:8088/origin/playlists/friends_ad2/perf*adindex.m3u8*369, due to: connect timed out'
    reg=r'playlists(/.*),'
    print replace_string(str1,reg,'')
    #print matched_string(str1,reg)
    #print string.replace(str1, matched_string(str1,reg)[0], '')
 '''   
