#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-2-21
@summary: This script is to setup VOD response template

@author: yanyang.xie
'''
import getopt
import os
import sys
import requests

# ads simulator server info
ads_server_host = '127.0.0.1'
ads_server_port = 8088
ads_server_context = 'spotlink-router/adsrs/'
ads_zone = None

# VOD template file and poid replace setting
vod_replace_poid_count = -1
vod_template_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'vod-response-template.xml'

def set_vod_response_template(i_headers={}):
    # i_headers = {"Content-Type":"application/xml"}
    set_url = ads_server_url + set_vod_response_template_api
    response_string = ''
    
    fs = open(vod_template_file_path)
    lines = fs.readlines()
    for line in lines:
        response_string += line
    
    print '#' * 60
    print 'Set VOD response template url: %s ' % (set_url)
    print 'VOD response template file path: %s ' % (vod_template_file_path)
    print 'VOD response template content:\n %s' % (response_string)
    print post(set_url, response_string, i_headers)

def get_response_template():
    print '#' * 60
    print 'Get VOD response template url: %s ' % (ads_server_url + get_vod_response_template_api)
    
    response = get(ads_server_url + get_vod_response_template_api)
    print 'Current VOD response template content in ads simulator:\n %s' % (response)

def clear_response_template():
    print '#' * 60
    print 'Clear VOD response template url: %s ' % (ads_server_url + clear_vod_response_template_api)
    print get(ads_server_url + clear_vod_response_template_api)

def get_response_poid_replace_count():
    print '#' * 60
    print 'Get VOD response poid replace count url: %s ' % (ads_server_url + get_vod_poid_replace_count)
    print get(ads_server_url + get_vod_poid_replace_count)

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
    print 'setup_vod_response.py usage:'
    print '-h: help message.'
    print '-H: ads simulator host, default is %s' % (ads_server_host)
    print '-P, ads simulator port, default is %s' % (ads_server_port)
    print '-C, ads simulator context path, default is %s' % (ads_server_context)
    print '-F, vod response template file absolute path, default is %s' % (vod_template_file_path)
    print '-Z, vod zone, default is \'\''
    print '-T, vod time based, default is false'
    print '-R, replace count of request-poid in vod response template, default is %s which is means just use the request poid number as this parameter.' % (vod_replace_poid_count)

def read_vod_parameters():
    global ads_server_host, ads_server_port, ads_server_context, vod_template_file_path, vod_replace_poid_count, ads_zone, ads_time_based
    opt_dict = read_opts(['-H', '-P', '-F', '-R', '-Z', '-T'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-H'):
            ads_server_host = opt_dict['-H']
    
        if opt_dict.has_key('-P'):
            ads_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-C'):
            ads_server_context = opt_dict['-C']
        
        if opt_dict.has_key('-F'):
            vod_template_file_path = opt_dict['-F']
            
        if opt_dict.has_key('-R'):
            vod_replace_poid_count = opt_dict['-R']
        
        if opt_dict.has_key('-Z'):
            ads_zone = opt_dict['-Z']

        if opt_dict.has_key('-T'):
            ads_time_based = opt_dict['-T']
        else:
            ads_time_based = 'true'

        return True

if __name__ == '__main__':
    # read_parameters
    if not read_vod_parameters():
        sys.exit(0)
        
    # ads server url and apis
    ads_server_url = 'http://%s:%s/%s' % (ads_server_host, ads_server_port, ads_server_context)
    set_vod_response_template_api = 'SetResponseTemplate/%s' % (vod_replace_poid_count)
    i_headers = {'zone':ads_zone} if ads_zone is not None else {}
    i_headers['timebase'] = ads_time_based if ads_time_based is not None and (ads_time_based == 'true' or ads_time_based == 'True')else 'false'

    clear_vod_response_template_api = 'ClearVODResponseTemplate'
    get_vod_response_template_api = 'GetVODResponseTemplate'
    get_vod_poid_replace_count = 'GetVODReplaceCount'
    
    # clear_response_template()
    set_vod_response_template(i_headers)
    get_response_template()
    get_response_poid_replace_count()
