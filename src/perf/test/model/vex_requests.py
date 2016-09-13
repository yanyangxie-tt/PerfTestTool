import requests


class VEXRequest(object):
    def  __init__(self,):
        self.response_logger_formatter = '%s response for task[%s]:\n%s'
    
    def get_response(self, task, timeout=3):
        return requests.get(task.get_url(), headers=task.get_request_headers(), timeout=timeout)
    
    def response_wapper(self, response_text):
        return '[[%s]]' % (response_text)
        
