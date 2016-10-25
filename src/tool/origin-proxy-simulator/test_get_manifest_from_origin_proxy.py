#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-13
@summary: This script is to test get data from origin proxy

@author: yanyang.xie
'''


import getopt
import json
import sys
import urllib
import urllib2

def get(url, headers={}, timeout=3):
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req, timeout=timeout)
    return response.read()

origin_server_host = '172.31.9.14'
origin_server_port = 8090

validate_url = 'http://%s:%s/origin/playlists/friends/index.m3u8' % (origin_server_host, origin_server_port)
variant_response = get(validate_url)

print variant_response