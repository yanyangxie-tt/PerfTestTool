#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
@author: yanyang.xie@thistech.com
@version: 0.1
@since: 11/25/2013
'''
import getopt
import random
import re
import sys
import time
import urllib
import urllib2


# mock origin server info
origin_server_host = '127.0.0.1'
origin_server_port = 8080
linear_channel_name = ''  # 'friends'
linear_ad_separation_segments = ''  # '4/3'

def post_linear_ad_insertion(linear_channel_name):
    request_url = 'http://%s:%s/origin/api/ads/%s/%s' %(origin_server_host, origin_server_port, linear_channel_name, linear_ad_separation_segments)
    request_hearders = {"Content-Type":"application/json"}
    print '\n' + '#' * 50
    print 'Linear AD insertion: \nRequest url:%s \nRequest header:%s ' % (request_url, request_hearders)
    print post(request_url, headers = request_hearders)

def check_linear_ad_insertion(linear_channel_name):
    validate_url = 'http://%s:%s/origin/playlists/%s/index.m3u8' % (origin_server_host, origin_server_port, linear_channel_name)
    variant_response = get(validate_url)
    print '#' * 50
    print 'Check linear channel response for %s using url %s' %(linear_channel_name, validate_url)
    print 'Linear variant response for %s:\n%s' % (linear_channel_name, variant_response)
    
    for line in variant_response.split('\n'):
        if line.find('m3u8') > 0:
            bit_rate_url = 'http://%s:%s/origin/playlists/%s/%s' % (origin_server_host, origin_server_port, linear_channel_name, line)
            bit_response = get(bit_rate_url)
            print 'Linear bit rate response for %s:\n%s' % (linear_channel_name, bit_response)
            break

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

# get test content list
def generate_test_content_list(content_names):
    p = r'(\w*\W*)\[(\d+)~(\d+)\]' #match test_[1,13]
    test_content_list = []
    
    for c_name in content_names.split(','):
        t = re.findall(p,c_name)
        if len(t) > 0:
            test_content_list += [t[0][0] + str(i) for i in range(int(t[0][1]), 1 + int(t[0][2]))]
        else:
            test_content_list.append(c_name)
    return test_content_list

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
    print 'setup__linear_ad_segments.py usage:'
    print '-h: help message.'
    print '-H: Mock origin server host, default is %s' % (origin_server_host)
    print '-P, Mock origin server port, default is %s' % (origin_server_port)
    print '-C, Linear channel name, no default value. Sample value is friends. If regular expression [a~b] is found in name, then batched channel name will be generated. test_[1~13] --> test_1 ~ test_13'
    print '-S, Linear channel ad separation/segments, no default value. Sample value is 4/3'

def read_linear_parameters():
    global origin_server_host, origin_server_port, linear_channel_name, linear_ad_separation_segments
    opt_dict = read_opts(['-H', '-P', '-C', '-S'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-H'):
            origin_server_host = opt_dict['-H']
    
        if opt_dict.has_key('-P'):
            origin_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-C'):
            linear_channel_name = opt_dict['-C']
        
        if opt_dict.has_key('-S'):
            linear_ad_separation_segments = opt_dict['-S']
            
        return (origin_server_host, origin_server_port, linear_channel_name, linear_ad_separation_segments)

def check_linear_parameters(linear_channel_name, linear_ad_separation_segments):
    if linear_channel_name == '':
        print 'ERROR: Linear channel name should not be None. Please use -h for more help info.'
        return False
    
    if linear_ad_separation_segments == '':
        print 'ERROR: Linear channel ad separation/segments should not be None. Please use -h for more help info.'
        return False
    
    return True

if __name__ == '__main__':
    if not read_linear_parameters():
        sys.exit()
        
    origin_server_host, origin_server_port, linear_channel_name, linear_ad_separation_segments = read_linear_parameters()
    if not check_linear_parameters(linear_channel_name, linear_ad_separation_segments):
        sys.exit()
    
    linear_channel_name_list = generate_test_content_list(linear_channel_name)
    for linear_channel_name in linear_channel_name_list:
        post_linear_ad_insertion(linear_channel_name)
        time.sleep(random.Random().randint(10, 30))
    
    time.sleep(1)
    check_linear_ad_insertion(linear_channel_name_list[random.randint(0,len(linear_channel_name_list)-1)])