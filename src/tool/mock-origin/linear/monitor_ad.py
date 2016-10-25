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
origin_server_host = '54.169.10.119'  # '127.0.0.1'
origin_server_port = 8080
linear_channel_name = 't6_test_1'  # 'friends'

def check_linear_ad_insertion(linear_channel_name):
    validate_url = 'http://%s:%s/origin/playlists/%s/index.m3u8' % (origin_server_host, origin_server_port, linear_channel_name)
    variant_response = get(validate_url)
    print '#' * 50
    print 'Check linear channel response for %s using url %s' % (linear_channel_name, validate_url)
    print 'Linear variant response for %s:\n%s' % (linear_channel_name, variant_response)
    
    for line in variant_response.split('\n'):
        if line.find('m3u8') > 0:
            bit_rate_url = 'http://%s:%s/origin/playlists/%s/%s' % (origin_server_host, origin_server_port, linear_channel_name, line)
            
            while(True):
                bit_response = get(bit_rate_url)
                print 'Linear bit rate response for %s:\n%s' % (linear_channel_name, bit_response)
                time.sleep(6)
                continue

def get(url, headers={}, timeout=3):
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req, timeout=timeout)
    return response.read() 

if __name__ == '__main__':
    check_linear_ad_insertion(linear_channel_name)
