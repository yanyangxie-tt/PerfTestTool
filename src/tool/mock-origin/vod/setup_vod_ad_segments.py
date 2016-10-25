#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-6
@summary: This script is to setup VOD ad insertion for special VOD content

@author: yanyang.xie
'''
import getopt
import json
import random
import re
import sys
import time
import urllib
import urllib2


# mock origin server info
origin_server_host = '127.0.0.1'
origin_server_port = 8080
vod_content_name = ''  # 'vod_espn/king'
vod_ad_start_segments = ''  # '1,4'
validate_time_gap = 6

def post_vod_ad_insertion(vod_content_name):
    vod_ad_start_segment_list = vod_ad_start_segments.split(',')
    request_url = 'http://%s:%s/origin/api/vodcdvrAds' % (origin_server_host, origin_server_port)
    request_hearders = {"Content-Type":"application/json"}
    request_body = generate_vod_ad_insertion_request_body(vod_content_name, vod_ad_start_segment_list)
    print '\n' + '#' * 50
    print 'VOD AD insertion: \nRequest url:%s \nRequest header:%s \nRequest body:\n%s' % (request_url, request_hearders, request_body)
    post(request_url, request_body, request_hearders)  # post ad insertion

def check_vod_ad_insertion(vod_content_name):
    validate_url = 'http://%s:%s/origin/playlists/%s/index.m3u8' % (origin_server_host, origin_server_port, vod_content_name)
    variant_response = get(validate_url)
    print '#' * 50
    print 'Check vod AD insertion for vod content %s' % (vod_content_name)
    print 'VOD variant response for %s:\n%s' % (vod_content_name, variant_response)
    
    for line in variant_response.split('\n'):
        if line.find('m3u8') > 0:
            bit_rate_url = 'http://%s:%s/origin/playlists/%s/%s' % (origin_server_host, origin_server_port, vod_content_name, line)
            bit_response = get(bit_rate_url)
            print 'VOD bit rate response for %s:\n%s' % (vod_content_name, bit_response)
            break
    print '#' * 50

def generate_vod_ad_insertion_request_body(resource, adSignalList):
    body_dict = {}
    body_dict['resource'] = resource
    body_dict['adSignalList'] = [{'adStartSegment': adSignal} for adSignal in adSignalList]
    return json.dumps(body_dict)

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
    p = r'(\w+)\[(\d+)~(\d+)\](/\S+)' #match test_[1,13]
    test_content_list = []
    
    for c_name in content_names.split(','):
        t = re.findall(p,c_name)
        print c_name, t
        if len(t) > 0:
            test_content_list += [t[0][0] + str(i) + t[0][3] for i in range(int(t[0][1]), 1 + int(t[0][2]))]
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
    print 'setup_vod_ad_segments.py usage:'
    print '-h: help message.'
    print '-H: Mock origin server host, default is %s' % (origin_server_host)
    print '-P, Mock origin server port, default is %s' % (origin_server_port)
    print '-C, VOD content name, must not empty. Format is vod_***/king, such as vod_espn/king. If content name is matching the regular expression vod_[1~13]/king then vod_1/king, vod_2/king ~ vod_13/king will be batch inserted AD.'
    print '-S, VOD ad start segment list, no default value. Sample value is 1,2,3'

def read_vod_parameters():
    global origin_server_host, origin_server_port, vod_content_name, vod_ad_start_segments
    opt_dict = read_opts(['-H', '-P', '-C', '-S'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-H'):
            origin_server_host = opt_dict['-H']
    
        if opt_dict.has_key('-P'):
            origin_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-C'):
            vod_content_name = opt_dict['-C']
        
        if opt_dict.has_key('-S'):
            vod_ad_start_segments = opt_dict['-S']
            
        return (origin_server_host, origin_server_port, vod_content_name, vod_ad_start_segments)

def check_vod_parameters(vod_content_name, vod_ad_start_segments):
    if vod_content_name == '':
        print 'ERROR: VOD content name should not be None. Please use -h for more help info.'
        return False
    
    if vod_content_name.find('vod_') !=0 :
        print 'ERROR: VOD content name does not meet requirement such as vod_friends/king. Please use -h for more help info.'
        return False
    
    if vod_ad_start_segments == '':
        print 'ERROR: VOD AD start segments should not be None. Please use -h for more help info.'
        return False
    
    return True

if __name__ == '__main__':
    if not read_vod_parameters():
        sys.exit()
        
    origin_server_host, origin_server_port, vod_content_name, vod_ad_start_segments = read_vod_parameters()
    if not check_vod_parameters(vod_content_name, vod_ad_start_segments):
        sys.exit()
    
    vod_content_name_list = generate_test_content_list(vod_content_name)
    for vod_content_name in vod_content_name_list:
        try:
            post_vod_ad_insertion(vod_content_name)
        except:
            print 'Failed to post ad insertion for %s, retry it' %(vod_content_name)
            post_vod_ad_insertion(vod_content_name)
    
    time.sleep(2)
    check_vod_ad_insertion(vod_content_name_list[random.randint(0, len(vod_content_name_list) - 1)])
