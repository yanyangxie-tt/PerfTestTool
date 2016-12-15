# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com

from datetime import datetime
from utility import time_util

class RequestsTask(object):
    def __init__(self, url):
        self.url = url
    
    def get_url(self):
        return self.url
    
    def set_url(self, url):
        self.url = url

class ScheduledRequestsTask(RequestsTask):
    def __init__(self, url, start_date=None, delta_seconds=0, delta_milliseconds=0, timeout=7):
        super(ScheduledRequestsTask, self).__init__(url)
        self.delta_seconds = delta_seconds
        self.delta_milliseconds = delta_milliseconds
        self.timeout = timeout
        
        if start_date is not None:
            if type(start_date) is not datetime:
                raise Exception('start date must be date type')
            self.start_date = start_date
        else:
            self.start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=delta_seconds, delta_milliseconds=delta_milliseconds)
    
    def get_start_date(self):
        return self.start_date
    
    def set_start_date_by_delta(self, delta_seconds=0, delta_milliseconds=0):
        self.start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=delta_seconds, delta_milliseconds=delta_milliseconds)
    
    def set_start_date(self, start_date):
        if type(start_date) is not datetime:
            raise Exception('start date must be date type')
        self.start_date = start_date
    
    def get_timeout(self):
        return self.timeout

class VEXScheduleReqeustsTask(ScheduledRequestsTask):
    def __init__(self, url, client_ip, zone, location, bitrate_url=None, delta_seconds=0, delta_milliseconds=0, timeout=7):
        super(VEXScheduleReqeustsTask, self).__init__(url, delta_seconds=0, delta_milliseconds=delta_milliseconds, timeout=7)
        self.client_ip = client_ip
        self.zone = zone
        self.location = location
        self.bitrate_url = bitrate_url
        
        self.headers = {}
        self.headers['X-Forwarded-For'] = client_ip
        self.headers['Connection'] = 'keep-alive'
        self.headers['Cookie'] = 'zone=%s;location=%s' % (zone, location)
    
    def get_url(self):
        return self.bitrate_url if self.bitrate_url is not None else self.url
    
    def set_bitrate_url(self, burl):
        self.bitrate_url = burl
    
    def get_bitrate_url(self):
        return self.bitrate_url
    
    def get_request_headers(self):
        return self.headers
    
    def get_client_ip(self):
        return self.client_ip

    def clone(self):
        return VEXScheduleReqeustsTask(self.url, self.client_ip, self.zone, self.location, self.bitrate_url, self.delta_seconds, self.delta_milliseconds)

    def __repr__(self):
        return 'client_ip:%s, url:%s, bitrate_url:%s, start_date:%s' % (self.client_ip, self.url, self.bitrate_url, self.start_date)

if __name__ == '__main__':
    task = VEXScheduleReqeustsTask('url1', '1.1.1.1', 1, 1)
    c_task = task.clone()
    c_task.set_start_date_by_delta(delta_seconds=300)
    
    print task.get_start_date()
    print c_task.get_start_date()
    print task
