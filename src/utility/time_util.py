# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com
# https://docs.python.org/2/library/datetime.html

import datetime
import threading
import time

# get local now according to the current machine time
time_zone_gap = time.timezone
def get_local_now():
    return get_datetime_after(datetime.datetime.utcnow(), delta_seconds=time_zone_gap) if time_zone_gap > 0 else get_datetime_before(datetime.datetime.utcnow(), delta_seconds=time_zone_gap)

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
    
    t_format = "%Y-%m-%d %H:%M:%S"
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
t_lock = threading.RLock()
def string_2_datetime(time_string, t_format="%Y-%m-%d %H:%M:%S"):
    # datetime.datetime.strptime("2010-12-04T10:30:53", "%Y-%m-%dT%H:%M:%S")
    with t_lock:
        dt = datetime.datetime.strptime(time_string, t_format)
    return dt

def long_2_string(time_long, t_format="%Y-%m-%d %H:%M:%S"):
    return datetime_2_string(long_2_datetime(time_long), t_format)

def string_2_long(time_string, t_format="%Y-%m-%d %H:%M:%S"):
    return datetime_2_long(string_2_datetime(time_string, t_format))

# get the datetime of 00:00:00 in special day.
def get_current_day_start_date(d_time=datetime.datetime.utcnow(), t_format="%Y-%m-%d %H:%M:%S"):
    time_string = '%s-%s-%s 00:00:00' % (d_time.year, d_time.month, d_time.day)
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

# get time gap(millisecond). But make sure those two date are in the same year
def get_time_gap_in_milli_seconds(f_date, s_date):
    if type(f_date) is not datetime.datetime or type(s_date) is not datetime.datetime :
        print 'Warn, parameter t_datetime is not a datetime.datetime, please check'
        return ''
    
    if s_date > f_date:
        gap = s_date - f_date
    else:
        gap = f_date - s_date
        
    return (gap.days * 3600 * 24 + gap.seconds) * 1000 + gap.microseconds / 1000

def generate_time_reg_list(start_time_hour_before_now=0, end_time_hour_before_now=24, time_format="%Y-%m-%d-%H"):
    start_time_hour_before_now = int(start_time_hour_before_now)
    end_time_hour_before_now = int(end_time_hour_before_now)
    
    if end_time_hour_before_now <= start_time_hour_before_now:
        tmp = start_time_hour_before_now
        end_time_hour_before_now = start_time_hour_before_now
        start_time_hour_before_now = tmp
    
    current_date = datetime.datetime.utcnow()
    time_reg_list = []
    for t in range(start_time_hour_before_now, end_time_hour_before_now):
        time_reg = datetime_2_string(get_datetime_before(current_date, delta_hours=t), time_format)
        time_reg_list.append(time_reg)
    return time_reg_list

if __name__ == '__main__':
    print get_local_now()
    time.sleep(1)
    print get_local_now()
    
    dt = get_datetime_after()
    dt_5 = get_datetime_after(delta_hours=5)
    
    print type(dt), dt
    print type(dt_5), dt_5
    
    dt_string = datetime_2_string(dt)
    print type(dt_string), dt_string
    
    dt_convert = string_2_datetime(dt_string)
    print type(dt_string), dt_convert
    
    print get_time_gap_in_seconds(dt, dt_5)
    print get_time_gap_in_milli_seconds(dt, dt_5)
    
    print datetime_2_long(dt), datetime_2_long(dt_5)
    print long_2_datetime(datetime_2_long(dt)), long_2_datetime(datetime_2_long(dt_5))
    print type(long_2_datetime(datetime_2_long(dt))), type(long_2_datetime(datetime_2_long(dt_5)))
    
    print generate_time_reg_list()
