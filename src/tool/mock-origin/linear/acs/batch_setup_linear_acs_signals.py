'''
@author: yanyang.xie@thistech.com
'''
import os
import re
import string
import sys
import time
import uuid

import requests

origin_server_host = '127.0.0.1'
origin_server_port = '8080'
origin_server_context_path = '' #/origin

def reset_ACS_signals():
    acs_reset_url = "http://%s:%s%s/api/acs/reset" %(origin_server_host, origin_server_port, origin_server_context_path)
    print 'Reset all the ACS signal using %s' %(acs_reset_url)
    requests.get(acs_reset_url)

def post_ACS_notifications(acs_channel_name_list, acs_signal_start_utc_time, acs_signal_stop_utc_time):
    for acs_channel_name in acs_channel_name_list:
        post_ACS_notification_for_channel(acs_channel_name, acs_signal_start_utc_time, acs_signal_stop_utc_time)

def post_ACS_notification_for_channel(channel_name, start_utc, stop_utc):
    acs_notification_service_url = "http://%s:%s%s/notify/%s" %(origin_server_host, origin_server_port, origin_server_context_path, channel_name)
    acs_notification_message = get_ACS_notification_message(channel_name, start_utc, stop_utc)
    headers = {'Content-Type': 'application/xml', 'charset':'ISO-8859-1'}
    
    print '#' * 100
    print 'Send ACS notification using %s with message:\n%s' %(acs_notification_service_url, acs_notification_message)
    r = requests.post(acs_notification_service_url, data = acs_notification_message, headers = headers)
    print r.status_code, r.reason

def get_ACS_notification_message(channel_name, start_utc, stop_utc):  
    signal_id = 'BLACKOUT:' + str(uuid.uuid4())
    
    acs_notification_template = '''<?xml version="1.0" encoding="utf-8"?>
    <signal:SignalProcessingNotification xmlns:signal="urn:cablelabs:iptvservices:esam:xsd:signal:1" xmlns:adi3="urn:cablelabs:md:xsd:core:3.0" xmlns:common="urn:cablelabs:iptvservices:esam:xsd:common:1" xmlns:terms="urn:cablelabs:md:xsd:terms:3.0" xmlns:manifest="urn:cablelabs:iptvservices:esam:xsd:manifest:1" xmlns:offer="urn:cablelabs:md:xsd:offer:3.0" xmlns:ns6="http://www.cablelabs.com/namespaces/metadata/xsd/confirmation/2" xmlns:ns7="urn:cablelabs:iptvservices:esni:xsd:2" xmlns:content="urn:cablelabs:md:xsd:content:3.0" xmlns:vinz="http://www.thistech.com/schemas/vinz/1" xmlns:title="urn:cablelabs:md:xsd:title:3.0" xmlns:signaling="urn:cablelabs:md:xsd:signaling:3.0" xmlns:po="urn:cablelabs:md:xsd:placementopportunity:3.0" xmlns:this="http://www.thistech.com/schemas/common/1" xmlns:acs="http://www.thistech.com/schemas/acs/1" acquisitionPointIdentity="%s">
      <common:StatusCode classCode="0"/>
      <signal:ResponseSignal action="create" acquisitionPointIdentity="%s" acquisitionSignalID="%s" signalPointID="%s">
        <signaling:UTCPoint utcPoint="2014-11-03T01:06:55.735Z"/>
        <signaling:BinaryData signalType="SCTE35">/DBZAAAAAAAAAAAABQb+AAAAAABDAkFDVUVJQUJDRH/YAABRimAJLUJMQUNLT1VUOjkwNmE0MjcwLTYyZjUtMTFlNC1iMTc3LTAyOWIyMzM4ZTUyMBAAAIuiR5Q=</signaling:BinaryData>
        <signal:EventSchedule interval="PT0H0M30S">
          <signal:StartUTC utcPoint="%s"/>
          <signal:StopUTC utcPoint="%s"/>
        </signal:EventSchedule>
      </signal:ResponseSignal>
    </signal:SignalProcessingNotification>
    '''
    return acs_notification_template %(channel_name, channel_name, signal_id, signal_id, start_utc, stop_utc)
    
def get_ACS_channel_name_list(channel_name_reg):
    if channel_name_reg is None or channel_name_reg == '':
        return None
    
    channel_name_list = get_test_content_name_list(channel_name_reg)
    print 'ACS channel names:' + string.join(channel_name_list, ',')
    return channel_name_list

def load_properties(config_file):
    infos = {}
    if not os.path.exists(config_file):
        return {}
    
    pf = open(config_file, 'rU')
    for line in pf:
        if string.strip(line) == '' or string.strip(line) == '\n' or string.find(line, '#') == 0:
            continue
        line = string.replace(line, '\n', '')
        tmp = line.split("=", 1)
        values = tmp[1].split("#", 1)
        
        infos[string.strip(tmp[0])] = string.strip(values[0])
    pf.close()
    return infos

def get_test_content_name_list(content_names, offset=0):
    p = r'(.*)\[(\d+)~(\d+)\](/*\S*)' #match test_[1,13]
    test_content_list = []

    for c_name in content_names.split(','):
        t = re.findall(p,c_name)
        if len(t) > 0:
            test_content_list += [t[0][0] + str(i + offset) + t[0][3] for i in range(int(t[0][1]), 1 + int(t[0][2]))]
        else:
            test_content_list.append(c_name.strip())
    return test_content_list

def is_valid_date(date_string, date_format="%Y-%m-%dT%H:%M:%S.000Z"):
    try:
        time.strptime(date_string, date_format)
        return True
    except:
        return False

if __name__ == '__main__':
    # read configuration file
    config_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'config.properties'
    print config_file 
    if not os.path.exists(config_file):
        print 'Not found the configuration file ' + config_file  +  ' on current dir, please check.'
        sys.exit(1)    

    configured_values = load_properties(config_file)
    print configured_values
    origin_server_host = configured_values['origin_server_host'] if configured_values.has_key('origin_server_host') else '127.0.0.1'
    origin_server_port = configured_values['origin_server_port'] if configured_values.has_key('origin_server_port') else '8080'
    origin_server_context_path = configured_values['origin_server_context_path'] if configured_values.has_key('origin_server_context_path') else ''
    channel_names = configured_values['test_channel_names'] if configured_values.has_key('test_channel_names') else ''   
    acs_signal_start_utc_time = configured_values['acs_signal_start_utc_time'] if configured_values.has_key('acs_signal_start_utc_time') else ''
    acs_signal_stop_utc_time=configured_values['acs_signal_stop_utc_time'] if configured_values.has_key('acs_signal_stop_utc_time') else ''
   
    # get acs channel list
    acs_channel_list = get_ACS_channel_name_list(channel_names)
    if acs_channel_list is None or len(acs_channel_list) == 0:
        print 'Not found the ACS channel names, please check.'
        sys.exit(1)
    
    # setup ACS signals for all the configured channels
    if not is_valid_date(acs_signal_start_utc_time) or not is_valid_date(acs_signal_stop_utc_time):
        print 'Start time or stop time must follow the time format \"%Y-%m-%dT%H:%M:%S.000Z\", please check.'
        sys.exit(1)
    
    # reset all the ACS signals
    reset_ACS_signals()
    
    # post ACS notification
    post_ACS_notifications(acs_channel_list, acs_signal_start_utc_time, acs_signal_stop_utc_time)
