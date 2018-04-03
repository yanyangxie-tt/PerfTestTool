#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-2-21
@summary: This script is to setup dash origin template

@author: yanyang.xie
'''
import getopt
import os
import sys
import requests
import random

# dash origin server info
dash_origin_server_host = '127.0.0.1'
dash_origin_server_port = 8081
dash_origin_server_context = 'mpd/'
set_mpd_template_api = 'set?id='
get_mpd_template_api = 'get'
seed_tag = 'seed'

asset_id_tag = 'vod_asset_'
asset_number = 100

# VOD template file and poid replace setting
mpd_template_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'mpd-template.xml'

def postTemplates():
    response_string = ''
    fs = open(mpd_template_file_path)
    lines = fs.readlines()
    for line in lines:
        response_string += line
    
    for i in range (1, asset_number + 1):
        url = '%s%s%s%s' %(dash_origin_server_url, set_mpd_template_api, asset_id_tag, str(i))
        content = response_string
        content = content.replace(seed_tag, '%s%s' %(asset_id_tag, str(i)))
        
        print 'setup %s, url is :%s' %(str(i), url)
        post(url, content, timeout=10)

def getTempalte():
    url = '%s%s/%s%s' %(dash_origin_server_url, get_mpd_template_api, asset_id_tag, random.Random().randint(1,asset_number))
    print 'get: %s' %(url)
    print get(url)            

def post(url, data=None, headers={}, timeout=3):
    response = requests.post(url, data, headers=headers, timeout=timeout)
    return response.text

def get(url, headers={}, timeout=3):
    response = requests.get(url, headers=headers, timeout=timeout)
    return response.text

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
    print 'Usage:'
    print '-h: help message.'
    print '-H: dash origin host, default is %s' % (dash_origin_server_host)
    print '-P, dash origin port, default is %s' % (dash_origin_server_port)
    print '-C, dash origin context path, default is %s' % (dash_origin_server_context)
    print '-F, mpd template file absolute path, default is %s' % (mpd_template_file_path)
    print '-T, id tag of mpd, default is %s' % (asset_id_tag)
    print '-N, asset number, default is %s' % (asset_number)

def read_vod_parameters():
    global dash_origin_server_host, dash_origin_server_port, dash_origin_server_context, mpd_template_file_path, asset_id_tag, asset_number
    opt_dict = read_opts(['-H', '-P', '-F', '-I', '-N'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-H'):
            dash_origin_server_host = opt_dict['-H']
            print dash_origin_server_host
    
        if opt_dict.has_key('-P'):
            dash_origin_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-F'):
            mpd_template_file_path = opt_dict['-F']
            
        if opt_dict.has_key('-I'):
            asset_id_tag = opt_dict['-I']
        
        if opt_dict.has_key('-N'):
            asset_number = int(opt_dict['-N'])
        
        return True

if __name__ == '__main__':
    # read_parameters
    if not read_vod_parameters():
        sys.exit(0)
    
    # dash origin server url
    dash_origin_server_url = 'http://%s:%s/%s' % (dash_origin_server_host, dash_origin_server_port, dash_origin_server_context)    
    postTemplates()
    getTempalte()    
        
    
    

