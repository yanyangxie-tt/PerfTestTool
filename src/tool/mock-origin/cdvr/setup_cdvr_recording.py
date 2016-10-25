#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-18
@summary: This script is to setup cDVR recording

@author: yanyang.xie
'''
import datetime
import getopt
import random
import re
import sys
import time
import urllib
import urllib2
from xml.dom import minidom


# mock origin server info
origin_server_host = '127.0.0.1'
origin_server_port = 8080
origin_server_context_path = ''
#origin_server_context_path='/origin' 

utc_now = datetime.datetime.utcnow()
cdvr_recording_start_time = utc_now + datetime.timedelta(seconds=2)
cdvr_recording_stop_time = utc_now + datetime.timedelta(seconds=602)
cdvr_recording_id = None
remove_existed_recording = False

validate_response = False
validate_time_gap = 10

def posr_cdvr_recording(cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time):
    request_url = 'http://%s:%s%s/api/recording' % (origin_server_host, origin_server_port, origin_server_context_path)
    request_hearders = {"Content-Type":"application/xml"}
    request_body = generate_cdvr_recording_request_body(cdvr_recording_id, generate_cdvr_time_string(cdvr_recording_start_time), generate_cdvr_time_string(cdvr_recording_stop_time))
    print '\n' + '#' * 50
    print 'cDVR recording: \nRequest url:%s \nRequest header:%s \nRequest body:\n%s' % (request_url, request_hearders, request_body)
    print post(request_url, request_body, request_hearders)

def validate_cdvr_recording(cdvr_recording_id):
    variant_url = 'http://%s:%s%s/playlists/%s/index.m3u8' % (origin_server_host, origin_server_port, origin_server_context_path, cdvr_recording_id)
    variant_response = get(variant_url)
    print '#' * 50
    print 'validate cDVR recording for %s' % (cdvr_recording_id)
    print 'cDVR variant response for %s:%s' % (cdvr_recording_id, variant_response)
    
    for line in variant_response.split('\n'):
        if line.find('m3u8') > 0:
            bit_rate_url = 'http://%s:%s%s/playlists/%s/%s' % (origin_server_host, origin_server_port, origin_server_context_path, cdvr_recording_id, line)
            bit_response = get(bit_rate_url)
            print 'cDVR bit rate response for %s:\n%s' % (cdvr_recording_id, bit_response)
            break

# This method is to convert '2014-01-01 03:40:44' to '2014-01-01T03:40:44.000000Z'
def generate_cdvr_time_string(t_date):
    return t_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

# This method is to remove existed recording
def remove_existed_recording_by_id(cdvr_recording_id):
    request_url = 'http://%s:%s%s/playlists/removeRecording/%s' %(origin_server_host, origin_server_port, origin_server_context_path, cdvr_recording_id)
    get(request_url)

# This method is to convert '2014-01-01 03:40:44' to a datetime object
def string2time(strtime, time_format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.strptime(strtime, time_format)

# This method is to convert a datetime object to '2014-01-01 03:40:44'
def format_timestamp(t_time=None, time_format_seconds="%Y-%m-%d %H:%M:%S"):
    if t_time is None:
        t_time = datetime.datetime.now()
    return t_time.strftime(time_format_seconds)

def generate_cdvr_recording_request_body(recording_id, start_time, stop_time):
    doc = minidom.Document() 
    root_node = doc.createElement("recording") 
    doc.appendChild(root_node) 
    
    recording_node = doc.createElement("recordingId") 
    recording_text_node = doc.createTextNode(str(recording_id))
    recording_node.appendChild(recording_text_node)
    
    start_time_node = doc.createElement("start")
    start_time_text_node = doc.createTextNode(str(start_time))
    start_time_node.appendChild(start_time_text_node)
    
    stop_time_node = doc.createElement("stop")
    stop_time_text_node = doc.createTextNode(str(stop_time))
    stop_time_node.appendChild(stop_time_text_node)
    
    root_node.appendChild(recording_node)
    root_node.appendChild(start_time_node)
    root_node.appendChild(stop_time_node)
    
    return doc.toxml()

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
    print '-P: Mock origin server port, default is %s' % (origin_server_port)
    print '-S: cDVR recording start time, format is 2014-01-01 03:40:44, default is %s' % (format_timestamp(cdvr_recording_start_time))
    print '-E: cDVR recording end time, format is 2014-01-01 04:40:44, default is %s' % (format_timestamp(cdvr_recording_stop_time))
    print '-I: cDVR recording ID, must not empty. Format is cdvr_***, such as cdvr_espn. If recording id is matching the regular expression cdvr_[1~13] then cdvr_1, cdvr_2 ~ cdvr_13 will be batch recorded.'
    print '-T: cDVR recording length(seconds). Not required. If -T is set, it will cover the -E parameter and then recording end time will be start time plus recording length'
    print '-R, Whether to remove the existed recording(same recording id) before setup new recording or not, default is not. If the value is \'True\', then remove first.'
    print '-V, Whether to validate recording after post the request. Default is false. If the value is \'True\', then validate.'

def read_cdvr_parameters():
    global origin_server_host, origin_server_port, cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time, cdvr_recording_length, remove_existed_recording,validate_response
    opt_dict = read_opts(['-H', '-P', '-S', '-E', '-I', '-T', '-R', '-V'])[0]
    if opt_dict.has_key('-h'):
        usage()
        return False
    else:
        if opt_dict.has_key('-H'):
            origin_server_host = opt_dict['-H']
    
        if opt_dict.has_key('-P'):
            origin_server_port = opt_dict['-P']
        
        if opt_dict.has_key('-I'):
            cdvr_recording_id = opt_dict['-I']
        
        if opt_dict.has_key('-S'):
            cdvr_recording_start_time = string2time(opt_dict['-S'])
        
        if opt_dict.has_key('-E'):
            cdvr_recording_stop_time = string2time(opt_dict['-E'])
        
        if opt_dict.has_key('-T'):
            cdvr_recording_length = int(opt_dict['-T'])
            cdvr_recording_stop_time = cdvr_recording_start_time + datetime.timedelta(seconds=cdvr_recording_length)
            
        if opt_dict.has_key('-R'):
            if opt_dict['-R'] == 'True':
                remove_existed_recording = True
        
        if opt_dict.has_key('-V'):
            if opt_dict['-V'] == 'True':
                validate_response = True
        return origin_server_host, origin_server_port, cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time, remove_existed_recording,validate_response

if __name__ == '__main__':
    if not read_cdvr_parameters():
        sys.exit()
    
    origin_server_host, origin_server_port, cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time, remove_existed_recording,validate_response = read_cdvr_parameters()
    print origin_server_host, origin_server_port, cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time, remove_existed_recording,validate_response
    
    if cdvr_recording_id is None:
        print 'ERROR: cDVR recording ID, must not empty.'
        sys.exit()
    
    if cdvr_recording_id.find('cdvr_') != 0:
        print 'ERROR: cDVR recording ID must start with \'cdvr_\', please check it.'
        sys.exit()
    
    cdvr_recording_id_list = generate_test_content_list(cdvr_recording_id)
    for cdvr_recording_id in cdvr_recording_id_list:
        try:
            if remove_existed_recording:
                remove_existed_recording_by_id(cdvr_recording_id)
            posr_cdvr_recording(cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time)
        except:
            print 'Failed to do record %s, try it once more after 1 seconds' %(cdvr_recording_id)
            time.sleep(1)
            if remove_existed_recording:
                remove_existed_recording_by_id(cdvr_recording_id)
            posr_cdvr_recording(cdvr_recording_id, cdvr_recording_start_time, cdvr_recording_stop_time)
            
    if validate_response:
        print 'All the cDVR recording has been posted. Wait for a few seconds to validate recording'
        for i in range(validate_time_gap):
            print 'Waiting %s seconds...' %(i + 1)
            time.sleep(1)
        validate_cdvr_recording(cdvr_recording_id_list[random.randint(0, len(cdvr_recording_id_list) - 1)])
    print '#' * 50