#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
Export sysstat log info to excel info.
@author: yanyang.xie@thistech.com
@version: 0.1
@since: 12/12/2013
'''
import datetime
import os
import re
import string
import xlwt

current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# sysstat log is in /var/log/sa/
monitor_file = '/var/log/sa/sar' + current_date.split('-')[-1]
report_file_dir = '/tmp/system_monitor/'
report_file_name = 'sysstat-monitor-info-%s.xls' % (current_date)

# if you just want special monitor info, just set its title into filter list 
indicator_list = ['%usr', '%nice', '%sys', '%iowait', '%steal', '%idle', 'tcp-tw', 'totsck', 'cswch/s', 'rxpck/s', 'txpck/s']

total_content_sheet_name = 'all_monitor_info'
partial_content_sheet_name = 'partial_monitor_info'

current_content = None

# following list is all the monitoring indicator info list in sysstat log file, each monitoring indicator info will be set into one list
cpu_content_list = []
proc_content_list = []
pswpin_content_list = []
pgpgin_content_list = []
tps_content_list = []
frmpg_content_list = []
kbmemfree_content_list = []
kbswpfree_content_list = []
dentunusd_content_list = []
runq_sz_content_list = []
dev_content_list = []
totsck_content_list = []
rxpck_content_list = []

# Read the sysstat log info and then group those data into different monitoring indicator list
def read_file(monitor_file):
    global current_content
    if not os.path.exists(monitor_file):
        return
    
    pf = open(monitor_file, 'r')
    for line in pf:
        if string.strip(line) == '' or string.strip(line) == '\n':
            continue
        
        if line.find('LINUX RESTART') > 0:
            continue
        
        # if the line has monitoring indicator title, it should be the start line of the monitoring statistic info
        # so change the current content list to the monitoring indicator content list
        if line.find('%iowait') > 0:
            current_content = cpu_content_list
        elif line.find('proc') > 0:
            current_content = proc_content_list
        elif line.find('pswpin') > 0:
            current_content = pswpin_content_list
        elif line.find('pgpgin') > 0:
            current_content = pgpgin_content_list
        elif line.find('rtps') > 0:
            current_content = tps_content_list
        elif line.find('frmpg') > 0:
            current_content = frmpg_content_list
        elif line.find('kbmemfree') > 0:
            current_content = kbmemfree_content_list
        elif line.find('kbswpfree') > 0:
            current_content = kbswpfree_content_list
        elif line.find('dentunusd') > 0:
            current_content = dentunusd_content_list
        elif line.find('runq-sz') > 0:
            current_content = runq_sz_content_list
        elif line.find('DEV') > 0:
            current_content = dev_content_list
        elif line.find('totsck') > 0:
            current_content = totsck_content_list
        elif line.find('rxpck') > 0:
            current_content = rxpck_content_list
            
        if line.find('Average') == 0:
            current_content = None
        
        if current_content is not None:
            # each monitoring indicator info will be split every 4 hours and then monitoring indicator title occurs again
            # should ignore the monitoring indicator tile line if it is not appear in the first time
            if len(current_content) > 0 and is_title_line(line):
                continue
            current_content.append(generate_line_content_list(line))

#check whether the line is monitoring indicator title line or not
def is_title_line(line):
    titles = ['%iowait', 'proc', 'pswpin', 'pgpgin', 'rtps', 'frmpg', 'kbmemfree', 'kbswpfree', 'dentunusd', 'runq-sz', 'DEV', 'totsck', 'rxpck']
    for title in titles:
        if line.find(title) > 0:
            return True
    return False
    
def generate_line_content_list(line):
    timestamp_info = line.split(' ', 1)
    timestamp = timestamp_info[0].strip()
    t_content = timestamp_info[1].strip().replace('\n', '')
    t_content = re.split(r'\s+', t_content)
    return [timestamp] + t_content

# To the CPU monitoring indicator, only the 'all' statistics data is useful, so need to filter other data
def convert_cpu_content():
    if len(cpu_content_list) == 0:
        return []
    
    temp_cpu_content = []
    temp_cpu_content.append(cpu_content_list[0])
    
    for c_content in cpu_content_list:
        if 'CPU' in c_content:
            c_content.remove('CPU')
        
        if 'all' in c_content:
            c_content.remove('all')
            temp_cpu_content.append(c_content) 
    return temp_cpu_content

# To the rxpck monitoring indicator, if there are more network interface, the monitoring data will be more. 
# If we want to show the data using chart in excel for each network interface, need convert its format from two-dimension to one-dimension
def convert_rxpck_content_list():
    if len(rxpck_content_list) == 0:
        return []
    
    iface_set = set([])
    for content in rxpck_content_list[1:]:
        iface_set.add(content[1])
    
    new_titles = [rxpck_content_list[0][0]]
    for iface in iface_set:
        for title in rxpck_content_list[0][2:]:
            new_titles.append(iface + '-' + title)
    
    total_content = []
    total_content.append(new_titles)
    for i in range(len(rxpck_content_list)):
        total_content.append([])
    
    content_index = 1
    rxpck_content_list.remove(rxpck_content_list[0])
    for i in range(0, len(rxpck_content_list)):
        if i % len(iface_set) == 0:
            content_index += 1
        
        for j in range(len(rxpck_content_list[i])):
            value = rxpck_content_list[i][j]
            if re.match('[0-9]{2}:[0-9]{2}:[0-9]{2}', value) and value in total_content[i]:
                continue
            
            if value in iface_set:
                continue
            
            total_content[content_index].append(rxpck_content_list[i][j])
    
    t_content = []
    for content in total_content:
        if len(content) > 0:
            t_content.append(content)
    
    return t_content

# merge all the monitoring indicator data
def generate_total_content_list():
    whole_contents = (totsck_content_list, cpu_content_list, rxpck_content_list, proc_content_list, pswpin_content_list, pswpin_content_list,
                      pgpgin_content_list, tps_content_list, frmpg_content_list, kbmemfree_content_list,
                      kbswpfree_content_list, dentunusd_content_list, runq_sz_content_list, runq_sz_content_list, dev_content_list)
     
    max_content_length = 0
    for content_list in whole_contents:
        if len(content_list) > max_content_length:
            max_content_length = len(content_list)
    
    total_content_list = [[] for i in range(max_content_length + 1)]
    for content_list in whole_contents:
        if content_list is None or len(content_list) == 0:
            continue
        
        for i in range(len(content_list)):
            for value in content_list[i]:
                if re.match('[0-9]{2}:[0-9]{2}:[0-9]{2}', value):
                    if value in total_content_list[i]:
                        continue
                    else:
                        total_content_list[i].append(value)
                else:
                    total_content_list[i].append(value)
    return total_content_list

# Write the monitoring indicator info into local file
def write_to_excel(file_path, file_name, total_content_sheet_name, total_content_list, partial_content_sheet_name, filtered_content_list):
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    
    t_file = file_path + file_name
    if os.path.exists(t_file):
        os.remove(t_file)

    x_file = xlwt.Workbook()
    
    # write filtered monitor info
    total_content_sheet = x_file.add_sheet(partial_content_sheet_name)
    for i in range(len(filtered_content_list)):
        for j in range(len(filtered_content_list[i])):
            value = filtered_content_list[i][j]
            if is_number(value):
                total_content_sheet.write(i, j, float(filtered_content_list[i][j]))
            else:
                total_content_sheet.write(i, j, filtered_content_list[i][j])
    
    # write total monitor info
    total_content_sheet = x_file.add_sheet(total_content_sheet_name)
    for i in range(len(total_content_list)):
        for j in range(len(total_content_list[i])):
            value = total_content_list[i][j]
            if is_number(value):
                total_content_sheet.write(i, j, float(total_content_list[i][j]))
            else:
                total_content_sheet.write(i, j, total_content_list[i][j])
    
    # save excel into local
    x_file.save(file_path + file_name)

def is_number(a):
    try:
        float(a)
        return True
    except:
        return False

# just want to do statistics information in content_list
def filter_total_contents(total_content_list, content_title_list):
    content_titles = total_content_list[0]
    index_list = [0]  # timestamp title must be there
    
    for content_title in content_title_list:
        for title in content_titles:
            if title.find(content_title) >= 0:
                index_list.append(content_titles.index(title))
    
    if len(index_list) == 1:
        return []
    
    filtered_content_list = []
    for content in total_content_list:
        if content is None or len(content) == 0:
            continue
        
        tmp_content = []
        for index in index_list:
            if len(content) > index:
                tmp_content.append(content[index]) 
        filtered_content_list.append(tmp_content)
    return filtered_content_list

if __name__ == '__main__':
    #monitor_file = 'sar12'
    #report_file_dir = 'D:\\Work\\source\\test\\load\\vexbj\\'
    
    read_file(monitor_file)
    
    # The format of following monitor is special compared to other monitor info, need convert its format first
    cpu_content_list = convert_cpu_content()
    rxpck_content_list = convert_rxpck_content_list()
    
    total_content_list = generate_total_content_list()
    filtered_content_list = filter_total_contents(total_content_list, indicator_list)
    
    write_to_excel(report_file_dir, report_file_name, total_content_sheet_name, total_content_list, partial_content_sheet_name, filtered_content_list)
    
