#!/usr/bin/python
# coding:utf-8

'''
Created on 2015-10-21
@summary: This script is to setup AD redirect rule

@author: yanyang.xie
'''
import getopt
import os
import sys
import urllib
import urllib2

# cr simulator server info
cr_server_host = '127.0.0.1'
cr_server_port = 80
cr_server_context = ''

# VOD ad redirect rule
ad_redirect_rule_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'ad_redirect_rule.xml'
set_ad_redirect_rule_api = 'setAdRedirectRules'
get_ad_redirect_rule_api = 'getAdRedirectRules'
clear_ad_redirect_rule_api = 'clearAdRedirectRules'

def set_ad_redirect_rules(i_headers={}):
    #i_headers = {"Content-Type":"application/xml"}
    set_url = cr_server_url + set_ad_redirect_rule_api
    response_string = ''
    
    fs = open(ad_redirect_rule_file_path)
    lines = fs.readlines()
    for line in lines:
        response_string += line
    
    print '#' * 60
    print 'Set AD redirect rule url: %s ' % (set_url)
    print 'AD redirect rule file path: %s ' % (ad_redirect_rule_file_path)
    print 'AD redirect rule content:\n %s' % (response_string)
    print post(set_url, response_string, i_headers)

def get_ad_redirect_rule():
    print '#' * 60
    print 'Get AD redirect rule url: %s ' % (cr_server_url + get_ad_redirect_rule_api)
    
    response = get(cr_server_url + get_ad_redirect_rule_api)
    print 'Current AD redirect rules in cr simulator:\n %s' % (response)

def clear_ad_redirect_rule():
    print '#' * 60
    print 'Clear AD redirect rule url: %s ' % (cr_server_url + clear_ad_redirect_rule_api)
    print get(cr_server_url + clear_ad_redirect_rule_api)

def post(url, data=None, headers={}, timeout=30):
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
    print 'setup_vod_response.py usage:'
    print '-h: help message.'
    print '-H: cr simulator host, default is %s' %(cr_server_host)
    print '-P, cr simulator port, default is %s' %(cr_server_port)
    print '-C, cr simulator context path, default is %s' %(cr_server_context)
    print '-F, AD redirect rule file absolute path, default is %s' %(ad_redirect_rule_file_path)

def read_content_router_parameters():
    global cr_server_host, cr_server_port, cr_server_context, ad_redirect_rule_file_path
    opt_dict = read_opts(['-H', '-P', '-C', '-F',])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-H'):
            cr_server_host = opt_dict['-H']
    
        if opt_dict.has_key('-P'):
            cr_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-C'):
            cr_server_context = opt_dict['-C']
        
        if opt_dict.has_key('-F'):
            ad_redirect_rule_file_path = opt_dict['-F']
        return True

if __name__ == '__main__':
    # read_parameters
    if not read_content_router_parameters():
        sys.exit(0)
        
    # cr server url and apis
    cr_server_url = 'http://%s:%s/%s' % (cr_server_host, cr_server_port, cr_server_context)
    i_headers = {"Content-Type":"application/xml"}
    
    set_ad_redirect_rules(i_headers)
    get_ad_redirect_rule()
    #clear_ad_redirect_rule()
