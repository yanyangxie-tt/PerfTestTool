#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-18
@summary: This script is to create or copy linear/VOD/cDVR content from seed content

@author: yanyang.xie
''' 
import getopt
import os
import shutil
import string
import sys

def generate_content_list(seed_content_folder_path, dest_content_folder_list):
    for dest_content_path in dest_content_folder_list:
        print seed_content_folder_path, dest_content_path
        generate_content(seed_content_folder_path, dest_content_path)

def generate_content(seed_content_folder_path, dest_content_path):
    shutil.rmtree(dest_content_path, True)
    if os.path.exists(dest_content_path):
        print 'Designated content folder is existed, not create it once more.'
    else:
        print '#' * 60
        print 'Start to create new content %s from seed %s' % (dest_content_path, seed_content_folder_path)
        shutil.copytree(seed_content_folder_path, dest_content_path)
        src_string = seed_content_folder_path.split(os.sep)[-1]
        dest_string = dest_content_path.split(os.sep)[-1]
        
        # To vod and cdvr, replace string should be trim tag 'vod_' or 'cdvr_'
        src_string = src_string.replace('vod_','').replace('cdvr_','')
        dest_string = dest_string.replace('vod_','').replace('cdvr_','')
        print 'Rename file or replace content from %s to %s' %(src_string, dest_string)
        rename_file_and_content(dest_content_path, src_string, dest_string)
        
        print 'Finish to create new content %s from seed %s' % (dest_content_path, seed_content_folder_path)

def rename_file_and_content(local_dir, src_string, dest_string, topdown=False):
    for root, dirs, files in os.walk(local_dir, topdown):
        for file_name in files:
            f_name = os.path.splitext(file_name)[0]
            f_sufix = os.path.splitext(file_name)[1]
            f_name = f_name.replace(src_string, dest_string)
            
            src_file = root + os.sep + file_name
            dest_file = root + os.sep + f_name + f_sufix
            
            os.rename(src_file, dest_file)
            rename_content(dest_file, src_string, dest_string)

def rename_content(file_path, src_string, dest_string):
    try:
        new_lines = []
        pf = open(file_path, 'rU')
        original_lines = pf.readlines()
        
        for line in original_lines:
            if string.strip(line) == '' or string.strip(line) == '\n' or string.find(line, '#') == 0:
                new_lines.append(line)
            else:
                new_lines.append(line.replace(src_string, dest_string))
        
        wf = open(file_path, 'w+')
        wf.writelines(new_lines)
    except:
        pass
    finally:
        pf.close()
        wf.close()

def read_opts(short_param_list=[], long_param_list=[]):
    short_params = 'h'
    for param in short_param_list:
        short_params += param.replace('-', '').strip() + ':'
    
    long_params = ["help"]
    for param in long_param_list:
        long_params.append(param.replace('-', '').strip() + '=')
        
    opts, args = getopt.getopt(sys.argv[1:], short_params, long_params)
    
    opt_dict = {}
    for opt, value in opts:
        opt_dict[opt] = value
    
    return opt_dict, args

def usage():
    print 'create_data_content.py usage:'
    print 'This script is to create linear/VOD/cDVR content from seed content. Please take care, if designated is same as existed content, will not create any more.'
    print '-h: help message.'
    print '-S: Source seed content folder absolute path, no default value'
    print '-D, Designated new content folder name, no default value. New folder will be placed on current script folder.'
    print '-N, How many new contents will be created. If use this parameter, then this script will batch create content folders. New content folder name will like dest_1'
    print 'Demo usage: python create_data_content.py -S /data/content/vod/vod_xy -D vod_test -N 3; python create_data_content.py -S /data/content/hq -D test -N 13;'

def read_parameters():
    seed_content_folder_path, dest_content_folder_name, dest_content_number = None, None, None
    opt_dict = read_opts(['-S', '-D', '-N'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-S'):
            seed_content_folder_path = opt_dict['-S']
        
        if opt_dict.has_key('-D'):
            dest_content_folder_name = opt_dict['-D']
        
        if opt_dict.has_key('-N'):
            dest_content_number = int(opt_dict['-N'])
            
        return (seed_content_folder_path, dest_content_folder_name, dest_content_number)

def check_parameters(seed_content_folder_path, dest_content_folder_name):
    if seed_content_folder_path is None or seed_content_folder_path == '':
        print 'ERROR: Source seed content path should not be None. Please use -h for more help info.'
        return False
    
    if not os.path.exists(seed_content_folder_path):
        print 'ERROR: Source seed content patch %s is not exist. Please check.' % (seed_content_folder_path)
        return False
    
    if dest_content_folder_name is None or dest_content_folder_name == '':
        print 'ERROR: Designated content folder name should not be None. Please use -h for more help info.'
        return False
    
    return True

if __name__ == '__main__':
    if not read_parameters():
        sys.exit()
        
    seed_content_folder_path, dest_content_folder_name, dest_content_number = read_parameters()
    if not check_parameters(seed_content_folder_path, dest_content_folder_name):
        sys.exit()

    '''
    seed_content_folder_path = 'D:\\Work\\source\\test\\load\\vexbj\\envsetup\\mock-origin\\hq'
    dest_content_folder_name = 'test'
    dest_content_number = 3
    '''
    
    here = os.path.dirname(os.path.abspath(__file__))
    if dest_content_number is not None:
        dest_content_folder_list = [here + os.sep + dest_content_folder_name + '_' + str(i) for i in range(1, dest_content_number + 1)]
    else:
        dest_content_folder_list = [here + os.sep + dest_content_folder_name]

    generate_content_list(seed_content_folder_path, dest_content_folder_list)
