import requests

from utility import time_util


class VEXRequest(object):
    def  __init__(self,):
        self.response_logger_formatter = '%s response for task[%s]:\n%s'
    
    def get_response(self, task, timeout=3):
        now = time_util.get_local_now()
        response = requests.get(task.get_url(), headers=task.get_request_headers(), timeout=timeout)
        used = time_util.get_time_gap_in_milli_seconds(now, time_util.get_local_now())
        return response, used
    
    def response_wapper(self, response_text):
        return '[[%s]]' % (response_text)
        
