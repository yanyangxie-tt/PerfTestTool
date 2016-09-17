# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import re
import sys

import requests

from utility import time_util


class PSNEvents(object):
    def __init__(self, log_name=None):
        self.psn_url_formatter = 'http://%s:%s/vex-director/PlacementStatusNotification'
        
    def init_logger(self, logger):
        self.logger = logger
    
    def extract_psn_tracking_id(self, content):
        '''Get PSN tracking id'''
        p = r'\w*\W*ID=(.*),DURATION[\.\n]*'
        psn_info = re.findall(p, content)
        
        if psn_info is not None and len(psn_info) > 0:
            return psn_info[0]
    
    def schedule_psn_event(self, sched, psn_event_list, client_ip, psn_receiver_host, psn_receiver_port=80, timeout=2, tag=''):
        '''
        Schedule the first PSN event in psn_event_list, other events will be passed on the event.
        @param sched: apscheduler.scheduler.Scheduler
        @param psn_event_list: {'event delay time from now: tracking id'}
        @param client_ip: client IP
        @param psn_receiver_host: psn receiver host
        @param psn_receiver_port: psn receiver port
        '''
        if len(psn_event_list) < 1:
            return
        
        try:
            psn_start_delay_second, psn_tracking_id = psn_event_list.pop(0)
            psn_start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=psn_start_delay_second + 1)
            self.logger.debug('Schedule %s PSN notification message at %s. IP: %s, tracking id: %s' % (tag, psn_start_date, client_ip, psn_tracking_id))
            sched.add_date_job(self.post_psn_notification, date=psn_start_date, args=(sched, psn_tracking_id, client_ip, psn_event_list, psn_receiver_host, psn_receiver_port, timeout, tag))
        except:
            exce_info = 'ERROR: Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
            self.logger.error(exce_info)
    
    def post_psn_notification(self, sched, ps_tracking_id, client_ip, psn_event_list, psn_receiver_host, psn_receiver_port=80, timeout=2, tag=''):
        url = self.psn_url_formatter % (psn_receiver_host, psn_receiver_port)
        i_headers = {"Content-Type":"application/xml"}
        i_headers['X-Forwarded-For'] = client_ip
        
        template = '''
            <adm:PlacementStatusNotification identity="86CF2E98-AEBA-4C3A-A3D4-616CF7D74A79" version="1.1"
                messageId="8648071A-9A9B-984B-5B55-3E8115349EC5"
                xmlns:adm="http://www.scte.org/schemas/130-3/2008a/adm"
                xmlns:core="http://www.scte.org/schemas/130-2/2008a/core">
                <adm:PlayData identityADS="1ea15585-1075-4833-86c6-9321695b5ce4">
                    <adm:SystemContext>
                        <adm:Session>1234</adm:Session>
                    </adm:SystemContext>
                    <adm:Client>
                        <adm:TerminalAddress type="DEVICEID">%s</adm:TerminalAddress>
                    </adm:Client>
                    <adm:SpotScopedEvents>
                        <adm:Spot>
                            <core:Content>
                                <core:Tracking>%s</core:Tracking>
                            </core:Content>
                        </adm:Spot>
                        <adm:Events>
                            <adm:PlacementStatusEvent time="2013-06-13T17:06:24.207Z" type="startPlacement"
                                messageRef="d10f868c-d44a-11e2-b1c2-00505601007a">
                                <adm:SpotNPT scale="1.0">0.05</adm:SpotNPT>
                            </adm:PlacementStatusEvent>
                        </adm:Events>
                    </adm:SpotScopedEvents>
                </adm:PlayData>
            </adm:PlacementStatusNotification>
        '''
        data = template % (client_ip, ps_tracking_id)
        self.logger.debug('Post PSN message to server. URL:%s. Headers:%s. Body:%s' % (url, str(i_headers), data))
        self.post(url, data, i_headers, timeout=timeout)
        
        # if have next PSN events in psn_event_list, need schedule a new event.
        if psn_event_list is not None and len(psn_event_list) > 0:
            self.schedule_psn_event(sched, psn_event_list, client_ip, psn_receiver_host, psn_receiver_port, timeout, tag)
    
    def schedule_end_all_psn_event(self, sched, session_id, end_all_psn_delay_second, psn_receiver_host, psn_receiver_port=80, tag=''):
        '''
        Schedule the first PSN event in psn_event_list, other events will be passed on the event.
        @param sched: apscheduler.scheduler.Scheduler
        @param psn_event_list: {'event delay time from now: tracking id'}
        @param client_ip: client IP
        @param psn_receiver_host: psn receiver host
        @param psn_receiver_port: psn receiver port
        '''
        
        if session_id is None or session_id.strip() == '':
            return
        
        try:
            end_all_psn_start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=int(end_all_psn_delay_second))
            self.logger.debug('Schedule %s PSN endAll notification message at %s. session ID: %s' % (tag, end_all_psn_start_date, session_id))
            sched.add_date_job(self.post_end_all_psn_notification, date=end_all_psn_start_date, args=(psn_receiver_host, psn_receiver_port, session_id))
        except:
            exce_info = 'ERROR: Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
            self.logger.error(exce_info)
    
    def post_end_all_psn_notification(self, psn_receiver_host, psn_receiver_port, session_id, timeout=2):
        url = self.psn_url_formatter % (psn_receiver_host, psn_receiver_port)
        i_headers = {"Content-Type":"application/xml"}
        
        template = '''
            <?xml version="1.0" encoding="utf-8" standalone="yes"?>
            <adm:PlacementStatusNotification identity="86CF2E98-AEBA-4C3A-A3D4-616CF7D74A79" version="1.1" messageId="69a360dd-4e8e-4af4-a333-52abc620e6c9" xmlns:adm="http://www.scte.org/schemas/130-3/2008a/adm" xmlns:core="http://www.scte.org/schemas/130-2/2008a/core">
                <adm:PlayData identityADS="1ea15585-1075-4833-86c6-9321695b5ce4">
                    <adm:SystemContext>
                        <adm:Session>%s</adm:Session>
                    </adm:SystemContext>
                    <adm:Client>
                        <adm:TerminalAddress type="DEVICEID">3962620500221861ed0501f21ea517d4</adm:TerminalAddress>
                        <adm:Events>
                            <adm:PlacementStatusEvent time="2014-06-28T19:56:19.653Z" type="endAll" messageRef="942bad6c-6a55-4dbb-9ff3-d3912c706049" />
                        </adm:Events>
                    </adm:Client>
                </adm:PlayData>
            </adm:PlacementStatusNotification>
        '''
        data = template % (session_id)
        self.logger.debug('Post PSN message to server. URL:%s. Headers:%s. Body:%s' % (url, str(i_headers), data))
        self.post(url, data, i_headers, timeout=timeout)
    
    def generate_psn_scheduled_event_list(self, psn_position_tracking_id_dict, psn_gap_list, segment_time=2):
        '''
        Generate PSN scheduled events list
        @param tracking_id_position_dict: {tracking_id:position,}
        @param psn_gap_list: psn gap list for one tracking id
        
        @return: PSN scheduled events list. [(time_gap_from_now, tracking id),]. 
        
        @note: time_gap_from_now is the starting time of PSN event compared to last psn time. 
        @note: If tracking info is in the current position for cdvr hot or linear, position should be 1
        '''
        
        if psn_position_tracking_id_dict is None or len(psn_position_tracking_id_dict) < 1:
            return []
    
        position_list = psn_position_tracking_id_dict.keys()
        position_list.sort(reverse=False)
        
        # get PSN delay interval between multiple PSN message for one tracking id
        psn_delay_interval_list = self._generate_psn_delay_interval(psn_gap_list)
        
        # get PSN delay seconds between all the tracking id.
        tracking_id_delay_seconds_dict = self._generate_tracking_id_delay_seconds_dict(position_list, psn_gap_list, segment_time)
        
        psn_event_list = []
        for position in position_list:
            delay_second = tracking_id_delay_seconds_dict[position]
            tracking_id = psn_position_tracking_id_dict[position]
            for index in range(0, len(psn_delay_interval_list)):
                if index == 0:
                    psn_event_list.append((delay_second + psn_delay_interval_list[index], tracking_id))
                else:
                    psn_event_list.append((psn_delay_interval_list[index], tracking_id))
        return psn_event_list
    
    def _generate_psn_delay_interval(self, psn_gap_list):
        psn_delay_interval_list = []
        if psn_gap_list is None or len(psn_gap_list) == 0:
            return psn_delay_interval_list
        
        psn_gap_index = 0
        for gap_index in range(0, len(psn_gap_list)):
            psn_gap = psn_gap_list[gap_index] - psn_gap_list[gap_index - 1] if gap_index > 0 else 0
            psn_delay_interval_list.append(psn_gap)
            psn_gap_index += 1
        
        return psn_delay_interval_list 
    
    def _generate_tracking_id_delay_seconds_dict(self, position_list, psn_gap_list, segment_time=2):
        '''@return: {psn_position: delay_seconds,}'''
        tracking_id_delay_seconds_dict = {}
        position_list.sort()
        
        max_psn_interval_for_one_trackingId = 0 if len(psn_gap_list) < 2 else (psn_gap_list[-1] - psn_gap_list[0])
        for p_index in range(len(position_list)):
            if p_index == 0:
                tracking_id_delay_seconds = psn_gap_list[0]
            else:
                tracking_id_delay_seconds = segment_time * (position_list[p_index] - position_list[p_index - 1]) - max_psn_interval_for_one_trackingId
                
            tracking_id_delay_seconds_dict[position_list[p_index]] = tracking_id_delay_seconds
        return tracking_id_delay_seconds_dict
    
    def post(self, url, data=None, headers={}, timeout=3):
        requests.post(url, data, headers=headers, timeout=timeout)

if __name__ == '__main__':
    psn = PSNEvents()
    psn_gap_list = [1, 31, 61]
    print psn._generate_psn_delay_interval(psn_gap_list)
    print psn._generate_tracking_id_delay_seconds_dict([0, 1200, 2400], psn_gap_list)
    
    tracking_id_position_dict = {1:'trackingId0', 201:'trackingId200', 401:'trackingId400', }
    print psn.generate_psn_scheduled_event_list(tracking_id_position_dict, psn_gap_list)
    
