# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com

import os
import re
import string
import sys

def get_config_value_by_key(config_dict, key, default_value=None):
    '''
    Get configured value by key from configuration value
    
    @param config_dict: configurations dict
    @param key: key in configurations dict
    @param default_value: default value if not found the key in configurations dict
    @return: string
    '''
    value = string.strip(config_dict[key]) if config_dict.has_key(key) else None
    if value is None and default_value is not None:
        value = default_value
    return value

def load_properties(config_file, ignore_line_by_start_tag='#', comment_tag_in_value='##'):
    '''
    Load configurations from configuration file
    
    @param config_file: configuration file in absolute path
    @param ignore_line_by_start_tag: if line started with #, ignore the line
    @param comment_tag_in_value: if find ## in value, ignore string after ##
    
    @return: configuration dict
    '''
    infos = {}
    if not os.path.exists(config_file):
        return {}
    
    with open(config_file, 'rU') as pf:
        for line in pf:
            if string.strip(line) == '' or string.strip(line) == '\n' or string.find(line, ignore_line_by_start_tag) == 0:
                continue
            line = string.replace(line, '\n', '')
            tmp = line.split("=", 1)
            
            values = tmp[1].split(comment_tag_in_value, 1)
            infos[string.strip(tmp[0])] = string.strip(values[0])
    return infos

def merge_properties(original_properties_file, change_properties_file):
    '''merge two property files, value in second file will replace the value in the first'''
    if not os.path.exists(original_properties_file):
        print 'The original file %s is not exist, do nothing' % (original_properties_file)
        return
    
    if not os.path.exists(original_properties_file):
        print 'The change file %s is not exist, do nothing' % (change_properties_file)
        return
    
    print 'replace content in %s by %s' % (original_properties_file, change_properties_file)
    original_dict = load_properties(original_properties_file)
    change_dict = load_properties(change_properties_file)
    original_dict.update(change_dict)
    
    os.remove(original_properties_file)
    lines = ['%s=%s\n' % (key, value) for key, value in original_dict.items()]
    with open(original_properties_file, 'w') as output:
        output.writelines(lines)
        
def get_script_current_dir():
    return os.path.split(os.path.realpath(sys.argv[0]))[0]

def matched_string(t_string, reg):
    return re.findall(reg, t_string)