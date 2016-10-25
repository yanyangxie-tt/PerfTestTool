#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
Distributed log analysis script
@author: yanyang.xie@thistech.com
@version: 0.2
@since: 7/14/4013
'''

import datetime
import os
import shutil
import string
import sys
import time
import traceback

from fabric.context_managers import cd, lcd
from fabric.decorators import parallel, task, roles
from fabric.operations import run, put, get, local
from fabric.state import env
from fabric.tasks import execute

import analysis_util as ay
import common_util
import time_util as tm


remote_script_tmp_dir = '/vex-tmp'
log_analysis_script_dir_name = 'log_analysis_script'
log_analysis_script_dir_path = remote_script_tmp_dir + '/' + log_analysis_script_dir_name 

remote_log_zip_file = 'log_analysis_zip_file.zip'
collect_script_file_name = 'collect_log.py'

here = os.path.dirname(os.path.abspath(__file__))
configs = common_util.get_configruations()
remote_filtered_log_dir = common_util.get_config_value_by_key(configs, 'remote_filtered_log_dir')
local_log_dir = common_util.get_config_value_by_key(configs, 'local_log_dir')

@task
@parallel
@roles('log_server')
def log_analysis_task():
    print env.host
    try:
        upload_script()
        
        zip_file_dir = local_log_dir + os.sep + string.replace(env.host, '.', '-')
        collect_and_download_log_file(zip_file_dir)
        analysis_log_file(zip_file_dir, remote_log_zip_file)
    except:
        traceback.print_exc()
        exce_info = 'Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
        print exce_info

# Upload script to remote server
def upload_script():
    print '#'*100
    print 'Upload script to remote server'
    
    run('rm -rf %s' % (log_analysis_script_dir_path), pty=False)
    run('mkdir -p %s' % (log_analysis_script_dir_path), pty=False)
    
    with cd(remote_script_tmp_dir):
        run('rm -rf %s' % (remote_log_zip_file), pty=False)
    
    with lcd(here):
        for t_file in os.listdir(here):
            if  t_file.split('.', 1)[1] == 'py' or t_file.split('.', 1)[1] == 'properties':
                try:
                    put(t_file, log_analysis_script_dir_path)
                except:
                    traceback.print_exc()

# collect logs from remote server and download it to local
def collect_and_download_log_file(zip_file_dir):
    print '#'*100
    print 'Execute script to collect logs from remote server'
    
    time.sleep(2)
    with cd(log_analysis_script_dir_path):
        run('python %s' % (collect_script_file_name), pty=False, quiet=False)
    
    
    if os.path.exists(zip_file_dir):
        print 'Clean local log dir %s' %(zip_file_dir)
        shutil.rmtree(zip_file_dir)
        time.sleep(1)
    os.mkdir(zip_file_dir)
    
    print 'Zip and download remote file %s into local folder %s' %(remote_log_zip_file, zip_file_dir)
    with cd(remote_filtered_log_dir):
        run('zip -r %s *' % (remote_log_zip_file), pty=False, quiet=False)
        run('cp %s %s' % (remote_log_zip_file, remote_script_tmp_dir))
    
    with cd(remote_script_tmp_dir):
        print zip_file_dir
        get(remote_log_zip_file, zip_file_dir + os.sep)

# analysis log files in local
def analysis_log_file(zip_file_dir, log_zip_file):
    unzip_file(zip_file_dir, log_zip_file)
    file_list = []
    for t_file in os.listdir(zip_file_dir):
        file_name, file_name_ext = tuple(os.path.splitext(t_file))
        if file_name_ext == '.zip':
            continue
        elif file_name_ext == '.gz':
            os.popen('gunzip %s' %(zip_file_dir + os.sep + t_file))
            file_list.append(zip_file_dir + os.sep + file_name)
        else:
            file_list.append(zip_file_dir + os.sep + t_file)
    
    print file_list
    # get log analysis time
    start_time_long, end_time_long = common_util.get_analysis_times(configs)
    
    # init local result dir
    local_result_dir = common_util.get_config_value_by_key(configs, 'local_result_dir')
    vex_componment_type = common_util.get_config_value_by_key(configs, 'type')
    if vex_componment_type is not None:
        local_result_dir += os.sep + vex_componment_type
    local_result_dir += os.sep + string.replace(env.host, '.', '-')
    today = tm.datetime_2_string(datetime.datetime.utcnow(), t_format='%Y-%m-%d')
    
    ay.analysis_log_files(file_list, local_result_dir, 'analysis-result-%s.txt' %(today), 'analysis-result-%s.xls' %(today), start_time_long, end_time_long)

def unzip_file(zip_file_dir, zip_file):
    import zipfile
    zfile = zipfile.ZipFile(zip_file_dir + os.sep + zip_file, 'r')
    for filename in zfile.namelist():
        data = zfile.read(filename)
        f = open(zip_file_dir + os.sep + filename, 'w+b')
        f.write(data)
        f.close()

def setKeyFile(key_filename):
    env.key_filename = key_filename
    
def setPassword(password):
    env.password = password

def setupFacricRoles(role, hosts_string, user='root', port=22):
    if role is None or hosts_string is None:
        return
    
    if hosts_string is not None and len(hosts_string) > 0:
        host_list = ['%s@%s:%s' % (user, host, port) for host in string.split(hosts_string, ',')]
        env.roledefs.update({role:host_list})

def init_fab_parameters():
    hosts = common_util.get_config_value_by_key(configs, 'hosts')
    user = common_util.get_config_value_by_key(configs, 'user')
    port = common_util.get_config_value_by_key(configs, 'port')
    pubkey = common_util.get_config_value_by_key(configs, 'pubkey')
    password = common_util.get_config_value_by_key(configs, 'password')
    
    setupFacricRoles('log_server', hosts, user, port)
    if pubkey is not None:
        setKeyFile(pubkey)
    else:
        setPassword(password)

def init_local_tmp_dir():
    configs = common_util.get_configruations()
    local_log_dir = common_util.get_config_value_by_key(configs, 'local_log_dir')
    if not os.path.exists(local_log_dir):
        os.makedirs(local_log_dir)

if __name__ == '__main__':      
    init_fab_parameters()
    init_local_tmp_dir()
    execute(log_analysis_task)
