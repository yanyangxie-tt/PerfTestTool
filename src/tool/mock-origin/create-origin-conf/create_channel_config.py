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
import traceback

here = os.path.dirname(os.path.abspath(__file__))
new_channel_config_file = 'new_config.properties'

def generate_configuration_list(seed_config_file_path, src_config_channel_name, dest_config_channel_name, dest_content_number):
    try:
        new_lines = []
        pf = open(seed_config_file_path, 'rU')
        seed_configuration_lines = pf.readlines()
        
        new_configurations = []
        if dest_content_number > 0:
            for i in range(1, dest_content_number + 1):
                dest_channel_name = dest_config_channel_name + '_' + str(i)
                new_configurations += generate_configuration(seed_configuration_lines, src_config_channel_name, dest_channel_name)
        else:
            new_configurations += generate_configuration(seed_configuration_lines, src_config_channel_name, dest_config_channel_name)
        
        wf = open(here + os.sep + new_channel_config_file, 'w+')
        wf.writelines(new_configurations)
        print 'New channel configurations has been exported to file %s' %(here + os.sep + new_channel_config_file)
    except:
        traceback.print_exc()
    finally:
        pf.close()
        wf.close()

def generate_configuration(seed_configuration_lines, src_config_channel_name, dest_config_channel_name):
    new_lines = []
    for line in seed_configuration_lines:
        new_lines.append(line.replace(src_config_channel_name, dest_config_channel_name))
    new_lines.append('\n')
    return new_lines
   
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
    print 'create_channel_config.py usage:'
    print 'This script is to create linear/VOD/cDVR configuration from seed configuration.'
    print '-h: help message.'
    print '-F: Source seed configuration file absolute path, no default value'
    print '-S: Source seed channel name, no default value. To linear, it should be the same as linear channel name. To VOD/cDVR, it should be the suffix name, take vod_friends for example, it should be friends.'
    print '-D, Designated new channel name, no default value.'
    print '-N, How many new configurations will be created. If use this parameter, then this script will batch create channel configurations. New channel name will like test_1'

def read_parameters():
    seed_config_file_path, src_config_channel_name, dest_config_channel_name, dest_content_number = None, None, None, None
    opt_dict = read_opts(['-F', '-S', '-D', '-N'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-F'):
            seed_config_file_path = opt_dict['-F']
        
        if opt_dict.has_key('-S'):
            src_config_channel_name = opt_dict['-S']
        
        if opt_dict.has_key('-D'):
            dest_config_channel_name = opt_dict['-D']
        
        if opt_dict.has_key('-N'):
            dest_content_number = int(opt_dict['-N'])
            
        return (seed_config_file_path, src_config_channel_name, dest_config_channel_name, dest_content_number)

def check_parameters(seed_config_file_path, dest_config_channel_name):
    if seed_config_file_path is None or seed_config_file_path == '':
        print 'ERROR: Source seed configuration file path should not be None. Please use -h for more help info.'
        return False
    
    if not os.path.exists(seed_config_file_path):
        print 'ERROR: Source seed configuration file %s is not exist. Please check.' % (seed_config_file_path)
        return False
    
    if dest_config_channel_name is None or dest_config_channel_name == '':
        print 'ERROR: Designated channel name should not be None. Please use -h for more help info.'
        return False
    
    return True

if __name__ == '__main__':
    if not read_parameters():
        sys.exit()
        
    seed_config_file_path, src_config_channel_name, dest_config_channel_name, dest_content_number = read_parameters()
    
    '''
    seed_config_file_path = here + os.sep + 'hq_channel_config_feed.txt'
    src_config_channel_name = 'hq'
    dest_config_channel_name = 'test'
    dest_content_number = 5
    '''
    if not check_parameters(seed_config_file_path, dest_config_channel_name):
        sys.exit()
    
    generate_configuration_list(seed_config_file_path, src_config_channel_name, dest_config_channel_name, dest_content_number)
