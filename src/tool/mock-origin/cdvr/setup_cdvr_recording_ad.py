#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-18
@summary: This script is to setup cDVR ad insertion for special cDVR content

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
cdvr_recording_id = ''  # 'cdvr_1'
cdvr_ad_start_segments = ''  # '1,4'
validate_response = False

read_response = False

def post_cdvr_ad_insertion(cdvr_recording_id):
    vod_ad_start_segment_list = cdvr_ad_start_segments.split(',')
    request_url = 'http://%s:%s/origin/api/vodcdvrAds' % (origin_server_host, origin_server_port)
    request_hearders = {"Content-Type":"application/json"}
    request_body = generate_cdvr_ad_insertion_request_body(cdvr_recording_id, vod_ad_start_segment_list)
    print '\n' + '#' * 50
    print 'cDVR AD insertion: \nRequest url:%s \nRequest header:%s \nRequest body:\n%s' % (request_url, request_hearders, request_body)
    post(request_url, request_body, request_hearders)

def generate_cdvr_ad_insertion_request_body(resource, adSignalList):
    body_dict = {}
    body_dict['resource'] = resource
    body_dict['adSignalList'] = [{'adStartSegment': adSignal} for adSignal in adSignalList]
    
    return json.dumps(body_dict)

def validate_cdvr_ad_insertion(cdvr_recording_id):
    validate_url = 'http://%s:%s/origin/playlists/%s/index.m3u8' % (origin_server_host, origin_server_port, cdvr_recording_id)
    variant_response = get(validate_url)
    print '#' * 50
    print 'Validate cdvr response for recording %s' % (cdvr_recording_id)
    print 'cDVR variant response for %s:\n%s' % (cdvr_recording_id, variant_response)
    
    for line in variant_response.split('\n'):
        if line.find('m3u8') > 0:
            bit_rate_url = 'http://%s:%s/origin/playlists/%s/%s' % (origin_server_host, origin_server_port, cdvr_recording_id, line)
            bit_response = get(bit_rate_url)
            print 'cDVR bit rate response for %s:\n%s' % (cdvr_recording_id, bit_response)
            break

def post(url, data=None, headers={}, timeout=15):
    req = urllib2.Request(url, headers=headers) 
    if data is not None: 
        try:
            data = urllib.urlencode(data)
        except:
            pass
    
    # enable cookie  
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor()) 
    opener.open(req, data, timeout=timeout)
    #response = opener.open(req, data, timeout=timeout)  
    #return response.read() 

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
    print 'setup_vod_response.py usage:'
    print '-h: help message.'
    print '-H: Mock origin server host, default is %s' % (origin_server_host)
    print '-P, Mock origin server port, default is %s' % (origin_server_port)
    print '-I, cDVR recording id, , must not empty. Format is cdvr_***, such as cdvr_espn. If recording id is matching the regular expression cdvr_[1~13] then recording cdvr_1, cdvr_2 ~ cdvr_13 will be batch added AD.'
    print '-S, cDVR ad start segment list, no default value. Sample value is 1,2,3'
    print '-V, Whether to validate ad insertion after post the ad request. Default is false. If the value is \'True\', then validate.'
    
def read_vod_parameters():
    global origin_server_host, origin_server_port, cdvr_recording_id, cdvr_ad_start_segments,validate_response
    opt_dict = read_opts(['-H', '-P', '-I', '-S', '-N', '-V'])[0]
    if opt_dict.has_key('-h'):
        usage()
    else:
        if opt_dict.has_key('-H'):
            origin_server_host = opt_dict['-H']
            
        if opt_dict.has_key('-P'):
            origin_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-I'):
            cdvr_recording_id = opt_dict['-I']
        
        if opt_dict.has_key('-S'):
            cdvr_ad_start_segments = opt_dict['-S']
        
        if opt_dict.has_key('-V'):
            if opt_dict['-V'] == 'True':
                validate_response = True
        
        return (origin_server_host, origin_server_port, cdvr_recording_id, cdvr_ad_start_segments,validate_response)

def check_vod_parameters(cdvr_recording_id, cdvr_ad_start_segments):
    if cdvr_recording_id == '':
        print 'ERROR: cDVR content name should not be None. Please use -h for more help info.'
        return False
    
    if cdvr_ad_start_segments == '':
        print 'ERROR: cDVR AD start segments should not be None. Please use -h for more help info.'
        return False
    
    return True

if __name__ == '__main__':
    if not read_vod_parameters():
        sys.exit()
        
    origin_server_host, origin_server_port, cdvr_recording_id, cdvr_ad_start_segments,validate_response = read_vod_parameters()
    if not check_vod_parameters(cdvr_recording_id, cdvr_ad_start_segments):
        sys.exit()
    
    if cdvr_recording_id is None:
        print 'ERROR: cDVR recording ID, must not empty.'
        sys.exit()
    
    if cdvr_recording_id.find('cdvr_') != 0:
        print 'ERROR: cDVR recording ID must start with \'cdvr_\', please check it.'
        sys.exit()
       
    cdvr_recording_id_list = generate_test_content_list(cdvr_recording_id)
    for cdvr_recording_id in cdvr_recording_id_list:
        try:
            post_cdvr_ad_insertion(cdvr_recording_id)
        except:
            print 'Failed to send recording AD for %s, retry it after 1 seconds' %(cdvr_recording_id)
            time.sleep(1)
            post_cdvr_ad_insertion(cdvr_recording_id)
    
    if validate_response:
        print 'All the cDVR recording AD insertion has been posted. Wait for a few seconds to validate recording'
        for i in range(2):
            print 'Waiting %s seconds...' %(i + 1)
            time.sleep(1)    
        validate_cdvr_ad_insertion(cdvr_recording_id_list[random.randint(0, len(cdvr_recording_id_list) - 1)])
    print '#' * 50
