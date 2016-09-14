# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import re
import shutil
import string
import sys
import time

def load_properties(config_file, ignore_line_by_start_tag='#'):
    '''
    Load configurations from configuration file
    
    @param config_file: configuration file in absolute path
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
            values = tmp[1].split("#", 1)
            infos[string.strip(tmp[0])] = string.strip(values[0])
    return infos

def get_file_dir_path(file_path):
    '''
    Get director path of current file
    
    @param file_path: file absolute path
    @return: directory name of current file
    '''
    return os.path.dirname(file_path)

def get_file_dir_name(file_path):
    '''
    Get dir name of current file
    
    @param file_path: file absolute path
    @return: directory name of current file
    '''
    current_dir_path = os.path.dirname(file_path)
    return os.path.split(current_dir_path)[1]

def get_matched_file_list(file_dir, file_name_reg=None, recur=True):
    '''
    Get matched file list in special dir
    
    @param file_dir: file dir
    @param file_name_reg: file name regular expression
    @param recur: whether to filter files in sub folder
    @return: file list
    '''
    file_list = []
    for root, dirs, files in os.walk(file_dir, recur):
        for t_file in files:
            if file_name_reg is not None:
                t = re.search(file_name_reg, str(t_file))
                if t:
                    file_list.append(root + os.sep + t_file)
            else:
                file_list.append(root + os.sep + t_file)
    return file_list

def filter_file_list(file_list, file_name_reg):
    '''
    Filter files in file list using regular expression, if file name is corresponding with regular expression, remove it
    
    @param file_list: file list
    @param file_name_reg: file name regular expression
    @return: filtered file list
    '''
    if type(file_list) not in [list, set]:
        return []
    
    files = []
    for t_file in file_list:
        t = re.search(file_name_reg, str(t_file))
        if not t:
            files.append(t_file)
    return files

def copy_file_2_dest(src_file_list, dest_dir, rm_exist_dest_dir=False):
    '''
        Copy file list into destined directory
        @param src_file_list: source file list
        @param dest_dir: destined directory
    '''
    if rm_exist_dest_dir and os.path.exists(dest_dir) :
        shutil.rmtree(dest_dir)
        time.sleep(1)
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    if dest_dir[-1] != os.sep:
        dest_dir += os.sep
    
    for src_file in src_file_list:
        src_file_name = string.split(src_file, os.sep)[-1]
        shutil.copyfile(src_file, dest_dir + src_file_name)


def copy_dir_2_dest(src_dir, dest_dir, copy_current_dir=False):
    # copy files and sub directory in src directory into dest directory
    # if copy_current_dir is True, then also copy the current src directory into dest directory
    
    src_dir = os.path.normpath(src_dir)
    dest_dir = os.path.normpath(dest_dir)
    
    if not os.path.exists(src_dir) or not os.path.exists(src_dir):
        print("Source is not exit")
        sys.exit(1)
        
    os.chdir(dest_dir)
    src_file = [os.path.join(src_dir, t_file) for t_file in os.listdir(src_dir)]
    for source in src_file:
        if os.path.isfile(source):
            shutil.copy(source, dest_dir)
        # 若是目录
        if os.path.isdir(source):
            p, src_name = os.path.split(source)
            sub_des_dir = os.path.join(dest_dir, src_name)
            shutil.copytree(source, sub_des_dir)

def read_file(file_path, read_size=None, mode='r'):
    '''
        Read file
        @param file_path: file absolute path
        @mode: file read mode. 'r','rU+'
        @param read_size: not read whole file at once, but read file every read_size
    '''
    if not os.path.exists(file_path):
        return None
    
    content = ''
    with open(file_path, mode) as file_object:
        if read_size is None:
            content = file_object.read()
        else:
            position = 0
            content += file_object.read(read_size)
            while True:
                if file_object.tell() <= position:
                    break
                position = file_object.tell()
                content += file_object.read(read_size)
    return content


def read_file_lines(file_path, mode='rU', read_size=None):
    if not os.path.exists(file_path):
        return None
    
    '''
        @param file_path: file abs path 
        @mode: file read mode. 'r','rU+'
        @param read_size: not read whole file at once, but read file every read_size
    '''
    lines = []
    with open(file_path, mode) as file_object:
        if read_size is None:
            lines = file_object.readlines()
        else:
            position = 0
            lines += file_object.readlines(read_size)
            while True:
                if file_object.tell() <= position:
                    break
                position = file_object.tell()
                lines += file_object.readlines(read_size)
    return lines

def write_file(out_file_dir, out_file_name, content, mode='a', is_delete=True):
    '''
        Write lines into file
        @param content: file content string or file content line list
        @param out_file_dir: out file directory 
        @param out_file_name: out file name
        @param mode: write file mode, 'w' or 'a'
        @param is_delete: whether delete exist file with same name before write new file
    '''
    if not os.path.exists(out_file_dir):
        os.makedirs(out_file_dir)

    if not out_file_dir[-1] == os.sep:
            out_file_dir += os.sep

    if is_delete and os.path.exists(out_file_dir + out_file_name):
        os.remove(out_file_dir + out_file_name)

    with open(out_file_dir + out_file_name, mode) as output:
        if type(content) == list:
            output.writelines(content)
        else:
            output.write(content)

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
            
if __name__ == '__main__':
    t_file = (__file__)
    print __file__
    print get_file_dir_path(t_file)
    print get_file_dir_name(t_file)
    print get_matched_file_list(get_file_dir_path(t_file), '.*file.*.py$')  # 获取所有文件名带c的py文件
    print filter_file_list(get_matched_file_list(get_file_dir_path(t_file)), '.*file.*.py')
    # print read_file_lines(t_file)[0:3]
    # print read_file(t_file, 20)
