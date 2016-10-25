#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
Load test script
@author: yanyang.xie@thistech.com
@version: 0.1
@since: 12/05/2013
'''

import datetime
import os

import psutil
from xlrd import open_workbook
import xlwt
from xlutils.copy import copy


#function of Get CPU State  
def get_system_cpu_percent(interval=3):
    return psutil.cpu_percent(interval)

#function of Get Memory  
def get_system_memory_percent():
    phymem = psutil.virtual_memory()
    return phymem.percent

#function of iostat: %user   %nice %system %iowait  %steal   %idle
def get_system_iostat(interval=3):
    iostat = psutil.cpu_times_percent(interval)
    return iostat.user, iostat.system, iostat.idle, iostat.iowait

#function of Get Process CPU State
def get_process_cpu_percent(pid, interval=3):
    p = psutil.Process(pid)
    return p.get_cpu_percent()

#function of Get Memory of special process
def get_process_memory_percent(pid):
    p = psutil.Process(pid)
    return p.get_memory_percent()

def getProcessId(server_name='tomcat'):
    out_lines = os.popen("ps gaux | grep %s | grep -v grep | awk '{print $2}'" %(server_name)).readlines()
    if out_lines is None or len(out_lines) == 0:
        return None
    else:
        return int(out_lines[0])

def write_to_excel(content_list, file_path='/tmp/system_monitor/'):
    file_name = 'monitor-info-%s.xls' %(datetime.datetime.now().strftime("%Y-%m-%d"))
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    
    if not os.path.exists(file_path + file_name):
        x_file = xlwt.Workbook()
        x_sheet = x_file.add_sheet('monitor_info')
        headers = ['Timestamp','CPU','Memory','iostat_user','iostat_system','iostat_idle','iostat_iowait']
        for i in range(len(headers)):
            x_sheet.write(0,i,headers[i])
        
        x_sheet.write(1,0,datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        for i in range(len(content_list)):
            x_sheet.write(1,i+1,content_list[i])
        x_file.save(file_path + file_name)
    else:
        rb = open_workbook(file_path+file_name,formatting_info=True)
        r_sheet = rb.sheet_by_index(0) # read only copy to introspect the file
        row_index = r_sheet.nrows
        
        wb = copy(rb) # a writable copy (I can't read values out of this, only write to it)
        w_sheet = wb.get_sheet(0) # the sheet to write to within the writable copy
        w_sheet.write(row_index,0,datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        for i in range(len(content_list)):
            w_sheet.write(row_index,i+1,content_list[i])
        wb.save(file_path + file_name)

def record_monitor_info():
    system_cpu_percent = get_system_cpu_percent()
    iostat_user, iostat_system, iostat_idle, iostat_iowait = get_system_iostat()
    system_memory_stat = get_system_memory_percent()
    #print system_cpu_percent, system_memory_stat, iostat_user, iostat_system, iostat_idle, iostat_iowait
    write_to_excel((system_cpu_percent, system_memory_stat, iostat_user, iostat_system, iostat_idle, iostat_iowait))

if __name__ == '__main__':
    record_monitor_info()