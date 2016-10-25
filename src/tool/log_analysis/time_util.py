#!/usr/bin/python  
# -*- coding=utf-8 -*-  

'''
@author: yanyang.xie@thistech.com
@version: 0.1
@since: 04/01/2014

https://docs.python.org/2/library/datetime.html
'''

import datetime
import time

# get datetime.datetime after now by a time_delta
def get_datetime_after(t_date=datetime.datetime.utcnow(), delta_seconds=0, delta_minutes=0, delta_hours=0, delta_days=0, delta_milliseconds=0):
    return t_date + datetime.timedelta(seconds=delta_seconds, minutes=delta_minutes, hours=delta_hours, days=delta_days, milliseconds=delta_milliseconds)

# get datetime.datetime after now by a time_delta
def get_datetime_before(t_date=datetime.datetime.utcnow(), delta_seconds=0, delta_minutes=0, delta_hours=0, delta_days=0, delta_milliseconds=0):
    return t_date - datetime.timedelta(seconds=delta_seconds, minutes=delta_minutes, hours=delta_hours, days=delta_days, milliseconds=delta_milliseconds)

# convert a datetime object to long
def datetime_2_long(t_datetime):
    if type(t_datetime) is not datetime.datetime:
        print 'Warn, parameter t_datetime is not a datetime.datetime, please check'
        return 0
    
    t_format="%Y-%m-%d %H:%M:%S"
    strtime = t_datetime.strftime(t_format)
    t_tuple = time.strptime(strtime, t_format)
    return time.mktime(t_tuple)

# convert a long to datetime object
def long_2_datetime(time_long):
    t_tuple = time.localtime(time_long)
    dt = datetime.datetime(*t_tuple[:6])
    return dt

# convert a datetime object to special format string
def datetime_2_string(t_datetime, t_format="%Y-%m-%d %H:%M:%S"):
    if type(t_datetime) is not datetime.datetime:
        print 'Warn, parameter t_datetime is not a datetime.datetime, please check'
        return ''
    
    return t_datetime.strftime(t_format)

# convert a string object to datetime object
def string_2_datetime(time_string, t_format="%Y-%m-%d %H:%M:%S"):
    # datetime.datetime.strptime("2010-12-04T10:30:53", "%Y-%m-%dT%H:%M:%S")
    return datetime.datetime.strptime(time_string, t_format)

def long_2_string(time_long, t_format="%Y-%m-%d %H:%M:%S"):
    return datetime_2_string(long_2_datetime(time_long), t_format)

def string_2_long(time_string, t_format="%Y-%m-%d %H:%M:%S"):
    return datetime_2_long(string_2_datetime(time_string, t_format))

def get_today(d_time=datetime.datetime.utcnow(), t_format="%Y-%m-%d %H:%M:%S"):
    time_string = '%s-%s-%s 00:00:00' %(d_time.year, d_time.month, d_time.day)
    return string_2_datetime(time_string, t_format)

# get time gap(seconds). But make sure those two date are in the same year
def get_time_gap_in_seconds(f_date, s_date):
    if type(f_date) is not datetime.datetime or type(s_date) is not datetime.datetime :
        print 'Warn, parameter t_datetime is not a datetime.datetime, please check'
        return ''
    
    if s_date > f_date:
        gap = s_date - f_date
    else:
        gap = f_date - s_date
    
    return gap.days * 3600 * 24 + gap.seconds

# get the closest to and less than int minutes. default is to get the closed time_gap(1) minute.
# t_date must be datetime
def get_closer_time_in_minute(t_date, time_gap=1):
    minute_gap = t_date.minute % time_gap
    return t_date - datetime.timedelta(minutes=minute_gap,seconds=t_date.second,milliseconds=t_date.microsecond/1000) 

# 1 minutes
def get_time_point_list(start_time_long, end_time_long, time_gap=1, time_format='%Y-%m-%d %H:%M:%S'):
    time_point_list = []
    for i in range(0, 1 + int(end_time_long - start_time_long)/(int(time_gap) * 60)):
        time_point_long = start_time_long + i * (time_gap * 60)
        time_point_list.append(long_2_string(time_point_long, time_format))
    
    return time_point_list

if __name__ == '__main__':
    utc_now = datetime.datetime.utcnow()
    time_gap = 5
    start_time = get_closer_time_in_minute(get_datetime_before_now(delta_days=1),time_gap)
    end_time = get_closer_time_in_minute(utc_now)
    
    start_time_long = datetime_2_long(start_time)
    end_time_long = datetime_2_long(end_time)
    
    print start_time, end_time
    time_point_list = get_time_point_list(start_time_long, end_time_long, time_gap)
    print time_point_list

if __name__ == '__main__2':
    t_gap = 5
    t = datetime.datetime.now()
    print t
    print get_closer_time_in_minute(t, t_gap)

if __name__ == '__main__1':
    dt = get_datetime_after_now()
    dt_5 = get_datetime_after_now(5, delta_hours=0)
    
    print type(dt), dt
    print type(dt_5), dt_5
    
    dt_string = datetime_2_string(dt)
    print type(dt_string), dt_string
    
    dt_convert = string_2_datetime(dt_string)
    print type(dt_string), dt_convert
    
    print get_time_gap_in_seconds(dt, dt_5)
    
    print datetime_2_long(dt), datetime_2_long(dt_5)
    print long_2_datetime(datetime_2_long(dt)), long_2_datetime(datetime_2_long(dt_5))
    print type(long_2_datetime(datetime_2_long(dt))), type(long_2_datetime(datetime_2_long(dt_5)))
