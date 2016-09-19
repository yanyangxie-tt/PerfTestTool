#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
Distributed load test script
@author: yanyang.xie@thistech.com
@version: 0.3
@since: 07/29/2014
'''
import string

from fabric.context_managers import cd, lcd
from fabric.contrib.files import exists
from fabric.decorators import task, parallel, roles
from fabric.operations import run, put, local
from fabric.tasks import execute

from init_script_env import *
from utility import fab_util, common_util

project_dir, package_path = here.split('src')
project_source_dir = project_dir + os.sep + 'src'

def read_configurations():
    if not os.path.exists(config_file):
        print 'Configuration file \'%s\' does not exist'
        exit(1)
    
    print 'Read configurtion files and setup fabric env'
    config_dict = common_util.load_properties(config_file)
    if os.path.exists(golden_config_file):
        config_dict.update(common_util.load_properties(golden_config_file))
    return config_dict

def set_fabric_env(config_dict):
    user = common_util.get_config_value_by_key(config_dict, 'test.machine.username', 'root')
    port = common_util.get_config_value_by_key(config_dict, 'test.machine.port', '22')
    pub_key = common_util.get_config_value_by_key(config_dict, 'test.machine.pubkey')
    password = common_util.get_config_value_by_key(config_dict, 'test.virtual.machine.password')
    test_machines = common_util.get_config_value_by_key(config_dict, 'test.machine.hosts')
    
    if pub_key is None and password is None:
        print 'pubkey and password must have one'
        exit(1)
    
    fab_util.set_roles(perf_test_machine_group, ['%s@%s:%s' % (user, host, port) for host in string.split(test_machines, ',')])   
    fab_util.set_key_file(pub_key)

@task
@parallel
@roles(perf_test_machine_group)
def stop_perf_test():
    fab_util.fab_shutdown_service(perf_test_type)

@task
@parallel
@roles(perf_test_machine_group)
def rm_perf_test_log():
    run('rm -rf %s' % (perf_test_remote_log_dir), pty=False)

@task
@parallel
@roles(perf_test_machine_group)
def start_perf_test():
    zip_perf_test_script()
    upload_test_script()
    with cd(perf_test_remote_script_dir + package_path):
        run('nohup python %s > %s' % (load_test_script_file_name, perf_test_remote_script_dir + package_path + '/perf_test.log'), shell=False, pty=True, quiet=False)

def upload_test_script():
    # create script folder in remote machine
    if exists(perf_test_remote_script_dir):
        run('rm -rf %s' % (perf_test_remote_script_dir))
    run('mkdir -p %s' % (perf_test_remote_script_dir))
    
    # upload zipped file to remote and then unzip
    with lcd(perf_test_script_zip_file_dir):
        put(perf_test_script_zip_name, perf_test_remote_script_dir)
    
    with cd(perf_test_remote_script_dir):
        run('unzip -o %s -d %s' % (perf_test_script_zip_name, perf_test_remote_script_dir))
        run('rm -rf %s/%s' % (perf_test_remote_script_dir, perf_test_script_zip_name))

def zip_perf_test_script():
    with lcd(project_source_dir):
        if os.path.exists(perf_test_script_zip_file_name):
            os.remove(perf_test_script_zip_file_name)
        
        zip_command = 'zip -r %s perf utility' % (perf_test_script_zip_file_name)
        local(zip_command)

set_fabric_env(read_configurations())

if __name__ == '__main__':              
    execute(stop_perf_test)
    execute(rm_perf_test_log)
    execute(start_perf_test)
    
