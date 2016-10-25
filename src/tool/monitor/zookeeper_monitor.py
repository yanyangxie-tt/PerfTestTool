#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
This script is to monitor zookeeper running status
@author: yanyang.xie@thistech.com
@version: 0.1
@since: 03/21/2014
'''

import datetime
import os
import time

from xlrd import open_workbook
from xlutils.copy import copy
import xlwt


command = 'echo stat | nc %s %s'

#please take care, 'bytes ' must have a apace ' ' word to distinguish bytes_written and bytes_read
zookeeper_mornitor_key = ['Latency min/avg/max','Received','Sent','Connections','Outstanding','Node count']

def get_zookeeper_status(m_ip='127.0.0.1', m_port=2181):
    mornitor_data = {}

    p = os.popen(command %(m_ip, m_port))
    lines = p.read().split('\n')
    for i in range(0, len(lines)-1):
        for mornitor_key in zookeeper_mornitor_key:
            if lines[i].find(mornitor_key)> -1:
                data = lines[i].split(':')[-1].strip()
                if str.isdigit(data):
                    data = int(data)
                mornitor_data[mornitor_key] = data
    return mornitor_data

def write_to_excel(content_dict, file_path='/tmp/system_monitor/'):
    file_name = 'zookeeper-monitor-info-%s.xls' %(datetime.datetime.now().strftime("%Y-%m-%d"))
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    if not os.path.exists(file_path + file_name):
        x_file = xlwt.Workbook()
        x_sheet = x_file.add_sheet('monitor_info')
        headers = zookeeper_mornitor_key
        for i in range(len(headers)):
            x_sheet.write(0,i+1,headers[i])

        x_sheet.write(1,0,datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        for i in range(len(zookeeper_mornitor_key)):
            x_sheet.write(1,i+1,content_dict[zookeeper_mornitor_key[i]])
        x_file.save(file_path + file_name)
    else:
        rb = open_workbook(file_path+file_name,formatting_info=True)
        r_sheet = rb.sheet_by_index(0) # read only copy to introspect the file
        row_index = r_sheet.nrows

        wb = copy(rb) # a writable copy (I can't read values out of this, only write to it)
        w_sheet = wb.get_sheet(0) # the sheet to write to within the writable copy
        w_sheet.write(row_index,0,datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        for i in range(len(zookeeper_mornitor_key)):
            w_sheet.write(row_index,i+1,content_dict[zookeeper_mornitor_key[i]])
        wb.save(file_path + file_name)

def record_monitor_info():
    zookeeper_mornitor_dict = get_zookeeper_status()
    print zookeeper_mornitor_dict
    write_to_excel(zookeeper_mornitor_dict)

if __name__ == '__main__':
    while(True):
        record_monitor_info()
        time.sleep(10)