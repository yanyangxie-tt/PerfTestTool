#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-19
@summary: This script is to create linear/VOD/cDVR bit rate lists

@author: yanyang.xie
'''

import traceback
import os
import getopt
import sys

header = '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-MEDIA-SEQUENCE:18\n#EXT-X-TARGETDURATION:6\n#EXT-X-ALLOW-CACHE:NO'
line_seperate = '#EXTINF:6.0,\n'

def create_ts_list(ts_prefix, ts_number):
    lines = [s + '\n' for s in header.split('\n')]
    for i in range(1, ts_number + 1):
        ts_assert = ts_prefix + '_0' + str(i) if i < 10 else ts_prefix + '_' + str(i)
        lines.append(line_seperate)
        lines.append(ts_assert + '\n')
    return lines

def write_to_file(file_path, lines):
    try:
        wf = open(file_path, 'w+')
        wf.writelines(lines)
        print 'Bit rate ts asserts has been exported to file %s' % (file_path)
    except:
        traceback.print_exc()
    finally:
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
    print 'create_bit_rate_ts_list.py usage:'
    print 'This script is to create linear/VOD/cDVR bit rate ts list. Ts result will be like xy_med_high_01.ts'
    print '-h: help message.'
    print '-P: TS prefix, such as xy_med_high. No default value. '
    print '-N, How many ts assets will be created.'

def read_parameters():
    ts_prefix, ts_number = None, None
    opt_dict = read_opts(['-P', '-N'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-P'):
            ts_prefix = opt_dict['-P']
        
        if opt_dict.has_key('-N'):
            ts_number = int(opt_dict['-N'])
            
        return (ts_prefix, ts_number)

def check_parameters(ts_prefix, ts_number):
    if ts_prefix is None or ts_prefix == '':
        print 'ERROR: TS prefix should not be None. Please use -h for more help info.'
        return False
    
    if ts_number is None or ts_number == '':
        print 'ERROR: TS number should not be None. Please use -h for more help info.'
        return False
    
    return True

if __name__ == '__main__':
    if not read_parameters():
        sys.exit()
        
    ts_prefix, ts_number = read_parameters()
    if not check_parameters(ts_prefix, ts_number):
        sys.exit()

    ts_contents = create_ts_list(ts_prefix, ts_number)
    write_to_file(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'bit_rate_ts_file.txt', ts_contents)
