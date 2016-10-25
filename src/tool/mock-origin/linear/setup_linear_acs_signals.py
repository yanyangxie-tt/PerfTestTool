'''
@author: yanyang.xie@thistech.com
'''
import datetime
import random
import time
import uuid

import requests


channel_name_list = ['friends']
#channel_name_list = ['t6_test_%s' %(i) for i in range(1, 250)]

#origin_server_url = 'http://121.201.2.49:8080/origin'
origin_server_url = 'http://localhost:8080'
origin_server_context_path = 'playlists'

start_time_after = 15 # seconds after now
stop_time_after = start_time_after + 30 # seconds after now

# get local now according to the current machine time
time_zone_gap = time.timezone
def get_local_now():
    return get_datetime_after(datetime.datetime.utcnow(),delta_seconds=time_zone_gap) if time_zone_gap > 0 else get_datetime_before(datetime.datetime.utcnow(), delta_seconds=time_zone_gap)

# get datetime.datetime after now by a time_delta
def get_datetime_before(t_date=datetime.datetime.utcnow(), delta_seconds=0, delta_minutes=0, delta_hours=0, delta_days=0, delta_milliseconds=0):
    return t_date - datetime.timedelta(seconds=delta_seconds, minutes=delta_minutes, hours=delta_hours, days=delta_days, milliseconds=delta_milliseconds)

# get datetime.datetime after now by a time_delta
def get_datetime_after(t_date=datetime.datetime.utcnow(), delta_seconds=0, delta_minutes=0, delta_hours=0, delta_days=0, delta_milliseconds=0):
    time_zone_gap = time.timezone
    return t_date + datetime.timedelta(seconds=delta_seconds, minutes=delta_minutes, hours=delta_hours, days=delta_days, milliseconds=delta_milliseconds)

# convert a datetime object to special format string
def datetime_2_string(t_datetime, t_format="%Y-%m-%d %H:%M:%S"):
    if type(t_datetime) is not datetime.datetime:
        print 'Warn, parameter t_datetime is not a datetime.datetime, please check'
        return ''
    
    return t_datetime.strftime(t_format)

def reset_ACS_signals(url):
    print 'Reset ACS singals using %s' %(url)
    requests.get(url)

def post_ACS_notification(service_url, channel_name, start_utc, stop_utc):
    acs_notification_message = get_ACS_notification_message(channel_name, start_utc, stop_utc)
    headers = {'Content-Type': 'application/xml', 'charset':'ISO-8859-1'}
    
    print 'Send ACS notification using %s with message:\n%s' %(service_url, acs_notification_message)
    r = requests.post(service_url, data = acs_notification_message, headers = headers)
    print r.status_code

def get_ACS_notification_message(channel_name, start_utc, stop_utc):  
    #<signal:StartUTC utcPoint="2014-11-03T01:06:55.735Z"/>
    #<signal:StopUTC utcPoint="2014-11-03T01:07:55.111Z"/>
    signal_id = 'BLACKOUT:' + str(uuid.uuid4())
    
    acs_notification_template = '''<?xml version="1.0" encoding="utf-8"?>
    <signal:SignalProcessingNotification xmlns:signal="urn:cablelabs:iptvservices:esam:xsd:signal:1" xmlns:adi3="urn:cablelabs:md:xsd:core:3.0" xmlns:common="urn:cablelabs:iptvservices:esam:xsd:common:1" xmlns:terms="urn:cablelabs:md:xsd:terms:3.0" xmlns:manifest="urn:cablelabs:iptvservices:esam:xsd:manifest:1" xmlns:offer="urn:cablelabs:md:xsd:offer:3.0" xmlns:ns6="http://www.cablelabs.com/namespaces/metadata/xsd/confirmation/2" xmlns:ns7="urn:cablelabs:iptvservices:esni:xsd:2" xmlns:content="urn:cablelabs:md:xsd:content:3.0" xmlns:vinz="http://www.thistech.com/schemas/vinz/1" xmlns:title="urn:cablelabs:md:xsd:title:3.0" xmlns:signaling="urn:cablelabs:md:xsd:signaling:3.0" xmlns:po="urn:cablelabs:md:xsd:placementopportunity:3.0" xmlns:this="http://www.thistech.com/schemas/common/1" xmlns:acs="http://www.thistech.com/schemas/acs/1" acquisitionPointIdentity="friends">
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
    return acs_notification_template %(channel_name, signal_id, signal_id, start_utc, stop_utc) 

def get_random_bit_rate_url(index_url, time_out=7, random_bitrate_url=True):
    r = requests.get(index_url, timeout=time_out)
    bite_url_info = r.text
    
    bite_url_list = []
    for line in bite_url_info.split('\n'):
        if line.strip() == '' or line.find('#') == 0:
            continue
        else:
            bite_url_list.append(line.replace('\r', ''))
    
    if len(bite_url_list) == 0:
        return None    
    
    if random_bitrate_url:
        u = bite_url_list[random.Random().randint(0, len(bite_url_list) - 1)]
    else:
        u = bite_url_list[0]
        
    return u

def get_linear_response(bitrate_request_url, stop_time_after, request_gap = 6):
    for i in range(1, 2 * stop_time_after + 1, request_gap):
        print '#' * 100
        print 'Call in the %s seconds:' %(i)
        r = requests.get(bitrate_request_url, timeout=5)
        print r.text
        time.sleep(request_gap)

if __name__ == '__main__':
    # reset all the ACS signals
    acs_reset_url = "%s/api/acs/reset" %(origin_server_url)
    reset_ACS_signals(acs_reset_url)
    
    # setup ACS signals for all the configured channels
    time_format="%Y-%m-%dT%H:%M:%S.000Z"
    current_date = datetime.datetime.utcnow()
    start_UTC = datetime_2_string(get_datetime_after(current_date, delta_seconds=start_time_after),time_format)
    stop_UTC = datetime_2_string(get_datetime_after(current_date, delta_seconds=stop_time_after),time_format)
    
    for channel_name in channel_name_list:
        service_url = "%s/notify/%s" %(origin_server_url, channel_name)
        post_ACS_notification(service_url, channel_name, start_UTC, stop_UTC)
    
    #check the first channel content
    time.sleep(2)
    channel_name = channel_name_list[0]
    index_request_url = '%s/%s/%s/%s' %(origin_server_url, origin_server_context_path, channel_name, 'index.m3u8')
    channel_bitrate_name = get_random_bit_rate_url(index_request_url, random_bitrate_url=False)
    bitrate_request_url = '%s/%s/%s/%s' %(origin_server_url, origin_server_context_path, channel_name, channel_bitrate_name)
    get_linear_response(bitrate_request_url, stop_time_after, 5)
