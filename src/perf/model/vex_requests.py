# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com

import requests
from utility import time_util

class VEXRequest(object):
    def  __init__(self,):
        pass
    
    def get_response(self, task, timeout=3):
        now = time_util.get_local_now()
        verify = "/Users/xieyanyang/Downloads/vod.comcast.net.crt"
        response = requests.get(task.get_url(), headers=task.get_request_headers(), timeout=timeout, verify=verify)
        used = time_util.get_time_gap_in_milli_seconds(now, time_util.get_local_now())
        return response, used
    
    @staticmethod
    def post(self, url, data, **kwargs):
        requests.post(url, data, kwargs)       
