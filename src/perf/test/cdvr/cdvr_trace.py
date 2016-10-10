# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import threading
from utility import time_util

class CdvrBitrateResult():
    '''Save one parsed bitrate response info'''
    
    def __init__(self, task, request_time, entertainment_number, ad_number, ad_url_list, ad_position_list):
        '''
        @param task: linear request task
        @param request_time: bitrate request time(datetime)
        @param entertainment_number: total entertainment ts number
        @param ad_number: total ad ts number
        @param ad_url_list: ad url list
        @param ad_position_list: ad start positions of all the ad break
        '''
        
        self.task = task
        self.request_time = request_time
        self.ad_number = ad_number
        self.ad_url_list = ad_url_list
        self.ad_position_list = ad_position_list
        self.entertainment_number = entertainment_number
        self.exist_ad = True if self.ad_number > 0 else False
    
    def __repr__(self):
        return '%s[%s]:entertainment number:%-2s, ad number:%-2s, ad position:-10%s' \
            % (self.task.get_client_ip(), self.request_time, self.entertainment_number, self.ad_number, self.ad_position_list)

class CdvrBitrateResultTrace():
    '''Traced one client bitrate requests and response, and then check the traced response'''
    def __init__(self, task, ad_insertion_frequency='200/20', content_segment_time=2, content_max_segment_number=300):
        '''
        @param task: linear request task
        @param ad_insertion_frequency: same as the ad_insertion_frequency in mock origin
        @param content_segment_time: time of one ts
        @param sequence_increase_request_number: how often that segment number must be increased.
                    Take t6linear for example, vex will do manifest expansion every 2 second and client call vex every second, 
                    so at least two request will make segment number increase by 1.
        '''
        
        self.lock = threading.RLock()
        self.task = task
        self.bitrate_url = task.get_bitrate_url()
        self.bitrate_result_list = []
        self.ad_insertion_frequency = ad_insertion_frequency
        self.content_segment_time = content_segment_time
        self.ad_number_in_complete_cycle = int(ad_insertion_frequency.split('/')[1])
        self.entertainment_number_in_ad_gap = int(ad_insertion_frequency.split('/')[0])
        self.content_max_segment_number = content_max_segment_number
        
        self.error_list = []
        self.is_fixed = False
        self.validated = False
    
    def fixed(self):
        self.is_fixed = True
        
    def add_bitrate_result(self, result):
        # store one bitrate result of one client
        if not isinstance(result, CdvrBitrateResult):
            return
        
        with self.lock:
            self.bitrate_result_list.append(result)
    
    def check(self, logger=None):
        if logger is not None:
            self.logger = logger
        
        if len(self.bitrate_result_list) == 0:
            return
        
        check = self.is_fixed
        exceed = False
        if check is False:
            # if time gap from start is larger than expected, must check
            first_record = self.bitrate_result_list[0]
            time_gap = time_util.get_time_gap_in_milli_seconds(first_record.request_time, time_util.get_local_now())
            if time_gap > self.content_max_segment_number * self.content_segment_time:
                check = True
                exceed = True
                self.validated = True

        if check is False:
            return
        
        if exceed:
            message = 'Recording has been running more than %s seconds, still not found endlist tag' % (self.content_max_segment_number * self.content_segment_time)
            self.record_error(message)
            return
        
        # 对目前的vex来说, 记录分段信息。因此只要过程中的一个bitrate错误，后续的bitrate content也会跟着出错，因此只需要check最后的一个bitrate content即可
        # for bitrate_recorder in self.bitrate_result_list:
        bitrate_recorder = self.bitrate_result_list[-1]
        entertainment_number = bitrate_recorder.entertainment_number
        ad_number = bitrate_recorder.ad_number
        ad_position_list = bitrate_recorder.ad_position_list
        
        if len(ad_position_list) == 0:
            if entertainment_number > self.entertainment_number_in_ad_gap:
                # 已经运行了，但是还没发现ad
                message = 'Recording has %s entertainment ts, but ad number is %s, less then expected %s.' \
                    % (entertainment_number, ad_number, self.ad_number_in_complete_cycle)
                self.record_error(message)
        else:
            # 第一次的ad位置不固定，但是之后的ad的间隔是固定的. 因此ad的数量是固定的
            first_ad_position = ad_position_list[0]
            expected_ad_number = self.ad_number_in_complete_cycle * (1 + ((entertainment_number - first_ad_position) / self.entertainment_number_in_ad_gap))
            if ad_number != expected_ad_number:
                message = 'Recording has %s entertainment ts, first ad position is %s, ad number is %s, not as expected %s. ad positions:[]' \
                    % (entertainment_number, first_ad_position, ad_number, expected_ad_number, ad_position_list)
                self.record_error(message)
            
            # 多过一段ad。那么每段ad的插入点的gap需要是self.entertainment_number_in_ad_gap
            for i, ad_position in enumerate(ad_position_list):
                if i + 1 < len(ad_position_list):
                    next_position = ad_position_list[i + 1]
                    if next_position - ad_position != self.entertainment_number_in_ad_gap:
                        message = 'AD gap is not as expected %s, ad positions is: %s' % (self.entertainment_number_in_ad_gap, ad_position_list)
                        self.record_error(message)
                        break
    
    def record_error(self, message):
        self.error_list.append(message)
        if self.logger: self.logger.error('%s:%s' % (self.task.get_client_ip(), message))
