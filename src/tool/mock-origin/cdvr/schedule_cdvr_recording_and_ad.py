'''
Created on 2014-3-24

@author: yanyang
'''

import datetime
import os
import string
import subprocess
import time

from apscheduler.scheduler import Scheduler

total_recording_nummer = 10000
hot_fixed_recording_rate='1:9'
hot_recording_perfix = 'cdvr_hot_'
fixed_recording_prefix = 'cdvr_fixed_'

hot_recording_schedule = 3600 # to let hot recording reset per 3600 seconds
hot_recording_time_length = 3600 # hot recording schedule time will be 1 hours
fixed_recording_time_length = 600 # fixed recording is just recorded 600 seconds
recording_ad_segments = string.join([str(1 + i * 200) for i in range(1200/200)],',')

origin_server_host = '54.255.146.85'
here = os.path.dirname(os.path.abspath(__file__))

def group_cdvr_ids(total_number, group_factor=10):
    ids_list = []
    size = total_number/group_factor if total_number%group_factor == 0 else total_number/group_factor + 1
    for i in range(size):
        start_number = i*group_factor
        end_number = (i+1)*group_factor
        if end_number >= total_number:
            end_number = total_number
        
        tmp_list = [i+1 for i in range(start_number, end_number)]
        ids_list.append(tmp_list)
    return ids_list

def generate_cdvr_content_name(start_number, end_number, prefix):
    return '%s[%s~%s]' %(prefix, start_number, end_number)

def generate_cdvr_content_name_list(total_number, prefix, group_factor=10):
    ids_list = group_cdvr_ids(total_number, group_factor)
    return [generate_cdvr_content_name(ids[0],ids[-1],prefix) for ids in ids_list]

def generate_cdvr_recording_id_number(total_recording_nummer, hot_fixed_recording_rate):
    rate_list = hot_fixed_recording_rate.split(':')
    
    hot_percent = float(rate_list[0])/(float(rate_list[0]) + float(rate_list[1]))
    fixed_percent = float(rate_list[1])/(float(rate_list[0]) + float(rate_list[1]))
    
    return int(total_recording_nummer * (hot_percent)), int(total_recording_nummer * (fixed_percent))

# Init scheduler
def init_cdvr_sched():
    cdvr_sched = Scheduler()
    cdvr_sched.daemonic = True
    
    sched_config = {'apscheduler.threadpool.core_threads':50,
           'apscheduler.threadpool.max_threads':200,
           'apscheduler.threadpool.keepalive':4,
           'apscheduler.misfire_grace_time':300,
           'apscheduler.coalesce':True,
           'apscheduler.max_instances':30000}
    cdvr_sched.configure(sched_config)
    cdvr_sched.start()
    return cdvr_sched

# Setup fixed recording and AD
def setup_cdvr_recording_and_ad(fixed_recording_ids, recording_length):
    os.chdir(here)
    fixed_recording_command = "python setup_cdvr_recording.py -H %s -I %s -T %s -R True -V False" %(origin_server_host,fixed_recording_ids,recording_length)
    p = subprocess.Popen(fixed_recording_command, shell=True)
    subprocess.Popen.wait(p)
    
    time.sleep(1)
    
    fixed_recording_ad_command = "python setup_cdvr_recording_ad.py -H %s -I %s -S %s -V False" %(origin_server_host,fixed_recording_ids,recording_ad_segments)
    p = subprocess.Popen(fixed_recording_ad_command, shell=True)
    subprocess.Popen.wait(p)
    print 'Finish to execute %s at %s' %(fixed_recording_command, datetime.datetime.utcnow())

if __name__ == '__main__':
    print '#'*50
    print 'Start to do cDVR recording on mock origin'
    cdvr_sched = init_cdvr_sched()
    
    total_hot_recording_number, total_fixed_recording_number = generate_cdvr_recording_id_number(total_recording_nummer, hot_fixed_recording_rate)
    hot_name_list = generate_cdvr_content_name_list(total_hot_recording_number, hot_recording_perfix, 20)
    fixed_name_list = generate_cdvr_content_name_list(total_fixed_recording_number, fixed_recording_prefix, 20)

    print hot_name_list
    print fixed_name_list

    #Setup fixed recording and AD
    print '#'*50
    print 'Start to do cDVR fixed recording on mock origin'
    start_utc_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
    for i in range(len(fixed_name_list)):
        if i%3==0:
            start_utc_date += datetime.timedelta(seconds=1)
        cdvr_sched.add_date_job(setup_cdvr_recording_and_ad, start_utc_date, args=(fixed_name_list[i],fixed_recording_time_length,))
    
    print 'Sleep %s seconds to execute hot recording' %(len(fixed_name_list))
    time.sleep(len(fixed_name_list)/50)
    print '#'*50
    print 'Start to do hot recording'
    start_utc_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
    for i in range(len(hot_name_list)):
        if i%3==0:
            start_utc_date += datetime.timedelta(seconds=1)
        cdvr_sched.add_interval_job(setup_cdvr_recording_and_ad, seconds=hot_recording_schedule, start_date=start_utc_date, args=(hot_name_list[i],hot_recording_time_length,))
    
    while(True):
        current_time = datetime.datetime.utcnow() + + datetime.timedelta(seconds=20)
        print (current_time - start_utc_date).seconds
        if (current_time - start_utc_date).seconds > 72000:
            print '#' * 100
            print 'Stop to schedule hot cdvr recording.'
            cdvr_sched.shutdown()
            break
        time.sleep(600)