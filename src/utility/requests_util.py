# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from contextlib import closing
import json
import os

import requests

class RequestsUtility(object):
    """
    Requests parameters:
    Constructs and sends a :class:`Request <Request>`.

    :param method: method for the new :class:`Request` object.
    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
    :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
    :param json: (optional) json data to send in the body of the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
    :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
    :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
        ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
        or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
        defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
        to add for the file.
    :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
    :param timeout: (optional) How long to wait for the server to send data
        before giving up, as a float, or a :ref:`(connect timeout, read
        timeout) <timeouts>` tuple.
    :type timeout: float or tuple
    :param allow_redirects: (optional) Boolean. Set to True if POST/PUT/DELETE redirect following is allowed.
    :type allow_redirects: bool
    :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
    :param verify: (optional) whether the SSL cert will be verified. A CA_BUNDLE path can also be provided. Defaults to ``True``.
    :param stream: (optional) if ``False``, the response content will be immediately downloaded.
    :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response

    Usage::

      >>> import requests
      >>> req = requests.request('GET', 'http://httpbin.org/get')
      <Response [200]>
    """
    
    def get_response(self, url, timeout=2, params=None, **kwargs):
        response = requests.get(url, params=params, timeout=timeout, **kwargs)
        return response
    
    def post(self, url, data=None):
        response = requests.post("http://httpbin.org/post", data=data)
        return response
    
    def post_json(self, url, data):
        response = requests.post(url, data=json.dumps(data))
        return response
    
    def post_files(self, url, file_list):
        files = {}
        for f in file_list:
            file_name = f.split('.')[-1]
            file[file_name] = open(f, 'rb')

        response = requests.post(url, files=files)
        return response
    
    def download_file(self, url, local_file_name=None, chunk_size=512 * 1024.0, **kwargs):
        '''
        Using Python requests lib to download file from remote
        @param url: download url
        @param local_file_name: local file name, if not set, using the downloading file name as local file name
        @param headers: request headers. format is {'Authorization':auth_token, }
        @param proxies: request proxies, format is {"http": "http://10.10.1.10:3128","https": "http://10.10.1.10:1080",}
        @param params: request parameters
        @param stream: whether to use streaming download
        @param chunk_size: max download bytes in each downloading reading
        '''
        
        if local_file_name is None:
            local_file_name = url.split('/')[-1]
        
        try:
            if os.path.exists(local_file_name):
                os.remove(local_file_name)
        except Exception, e:
            print e
            return
        
        # print kwargs
        if kwargs.get('stream') is True:
            with closing(requests.get(url, **kwargs)) as response:
                content_size = int(response.headers['content-length'])  # total content size
                progress = ProgressBar(local_file_name, total=content_size, running_status="Downloading", finished_status="Finished.")
                
                with open(local_file_name, "wb") as f:
                    for data in response.iter_content(chunk_size=int(chunk_size)):
                        f.write(data)
                        progress.refresh(current=len(data))
        else:
            with closing(requests.get(url, **kwargs)) as response:
                with open(local_file_name, "wb") as f:
                    for data in response.iter_content(chunk_size=int(chunk_size)):
                        f.write(data)

class ProgressBar(object):
    '''
    Downloading status bar, format is as follow:
    [title] running_status current/1024 KB total/1024 KB
    [vex-2.0.0-20140610.062448-284-release.zip] downloading 1024.00 KB / 32710.29 KB
    '''
    def __init__(self, title, current=0.0, running_status=None, finished_status=None, total=1000.0, sep='/'):
        super(ProgressBar, self).__init__()
        self.status_format = "[%s] %s %.2f %s %s %.2f %s %.2f%%"
        self.title = title
        self.total = total
        self.current = current
        self.status = running_status or ""
        self.finished_status = finished_status or " " * len(self.statue)
        self.unit = 'KB'
        self.chunk_size = 1024.0
        self.seq = sep

    def get_status(self):
        return self.status_format % (self.title, self.status, self.current / self.chunk_size, self.unit, self.seq, self.total / self.chunk_size, self.unit, 100 * self.current / self.total)

    def refresh(self, current=1, status=None):
        self.current += current
        # if status is not None:
        self.status = status or self.status
        end_str = "\r"
        if self.current >= self.total:
            end_str = '\n'
            self.status = status or self.finished_status
        print (self.get_status() + end_str)
