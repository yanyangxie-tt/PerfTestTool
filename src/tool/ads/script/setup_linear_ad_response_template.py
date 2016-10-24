#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-06-03
@summary: This script is to setup linear response template

@author: yanyang.xie
'''
import getopt
import os
import sys
import urllib
import urllib2

# ads simulator server info
ads_server_host = '127.0.0.1'
ads_server_port = 8088
ads_server_context = 'spotlink-router/adsrs/'
ads_zone = None
ads_location = None

# linear template file and poid replace setting
template_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'linear-response-template.xml'

def set_linear_response_template(i_headers={}):
    #i_headers = {"Content-Type":"application/xml"}
    set_url = ads_server_url + set_linear_response_template_api
    response_string = ''
    
    fs = open(template_file_path)
    lines = fs.readlines()
    for line in lines:
        response_string += line
    
    print '#' * 60
    print 'Set linear response template url: %s ' % (set_url)
    print 'Headers: %s' %(str(i_headers))
    print 'linear response template file path: %s ' % (template_file_path)
    print 'linear response template content:\n %s' % (response_string)
    print post(set_url, response_string, i_headers)

def get_response_template():
    print '#' * 60
    print 'Get linear response template url: %s ' % (ads_server_url + get_linear_response_template_api)
    
    response = get(ads_server_url + get_linear_response_template_api)
    print 'Current linear response template content in ads simulator:\n %s' % (response)

def clear_response_template():
    print '#' * 60
    print 'Clear Linear response template url: %s ' % (ads_server_url + clear_linear_response_template_api)
    print get(ads_server_url + clear_linear_response_template_api)

def post(url, data=None, headers={}, timeout=3):
    req = urllib2.Request(url, headers=headers) 
    if data is not None: 
        try:
            data = urllib.urlencode(data)
        except:
            pass
    
    # enable cookie  
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())  
    response = opener.open(req, data, timeout=timeout)  
    return response.read() 

def get(url, headers={}, timeout=3):
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req, timeout=timeout)
    return response.read() 

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
    print '-H: ads simulator host, default is %s' %(ads_server_host)
    print '-P, ads simulator port, default is %s' %(ads_server_port)
    print '-C, ads simulator context path, default is %s' %(ads_server_context)
    print '-F, linear response template file absolute path, default is %s' %(template_file_path)
    print '-Z, zone, no default value'
    print '-L, location, no default value'

def read_linear_parameters():
    global ads_server_host, ads_server_port, ads_server_context, template_file_path, ads_location,ads_zone
    opt_dict = read_opts(['-H', '-P', '-C', '-F', '-L','-Z'])[0]
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
            template_file_path = opt_dict['-F']
            
        if opt_dict.has_key('-L'):
            ads_location = opt_dict['-L']
        
        if opt_dict.has_key('-Z'):
            ads_zone = opt_dict['-Z']
            
        if ads_zone is None and ads_location is None:
            print 'Zone or location must be at least one.'
            return False
        
        return True

if __name__ == '__main__':
    # read_parameters
    if not read_linear_parameters():
        usage()
        sys.exit(0)
        
    # ads server url and apis
    ads_server_url = 'http://%s:%s/%s' % (ads_server_host, ads_server_port, ads_server_context)
    set_linear_response_template_api = 'SetResponseTemplate/%s' % (ads_location)
    
    i_headers = {}
    i_headers['channelType'] = 'linear'
    i_headers['zone'] = ads_zone if ads_zone != None else {}
    i_headers['location'] = ads_location if ads_location != None else {}
    
    clear_linear_response_template_api = 'ClearLinearResponseTemplate'
    get_linear_response_template_api = 'GetLinearResponseTemplate'
    
    #clear_response_template()
    set_linear_response_template(i_headers)
    get_response_template()
