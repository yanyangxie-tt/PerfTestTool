#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
Distributed load test script
@author: yanyang.xie@thistech.com
@version: 0.3
@since: 07/29/2014
'''
from fabric.context_managers import cd, lcd
from fabric.contrib.files import exists
from fabric.decorators import task, parallel, roles
from fabric.operations import run, put
from fabric.state import env
from fabric.tasks import execute

from init_script_env import *
from utility import fab_util

load_test_script_file_name = 'execute_multi_test.py'

remote_script_tmp_dir = '/tmp/vex-perf-test/'

here = os.path.abspath(os.path.dirname(__file__))
project_dir, package_path = here.split('src')
project_source_dir = project_dir + os.sep + 'src'

test_machines = '54.169.51.77'
public_key = '/Users/xieyanyang/work/ttbj/ttbj-keypair.pem'

server_role_name = 'load_test_server'

# fab_util.set_roles('load_test_server', ['%s@%s:%s' % ('root', host, '22') for host in string.split(test_machines, ',')])   
fab_util.set_roles(server_role_name, ['root@54.169.51.77:22', ])   
fab_util.set_key_file(public_key)
print env.roledefs
print env.key_filename

perf_test_script_zip_name = 'perftest.zip'
perf_test_script_zip_tmp_dir = '/tmp'
perf_test_script_zip_file = perf_test_script_zip_tmp_dir + os.sep + perf_test_script_zip_name

'''
with lcd(project_source_dir):
    if os.path.exists(perf_test_script_zip_file):
        os.remove(perf_test_script_zip_file)
    
    local('zip -r %s perf utility' % (perf_test_script_zip_file))
'''

@task
@parallel
@roles(server_role_name)
def kill_vod_test():
    fab_util.fab_shutdown_service('vod')


@task
@parallel
@roles('load_test_server')
def rm_vod_test_log():
    # remote_result_dir = common_util.get_test_case_tmp_result_dir(constants.result_dir, os.path.dirname(os.path.abspath(__file__)) + os.sep + 'config.properties')
    remote_log_dir = '/tmp/load-test-result-vod-perf'
    run('rm -rf %s' % (remote_log_dir), pty=False)

@task
@parallel
@roles(server_role_name)
def execute_load_test():
    # create script folder in remote machine
    if exists(remote_script_tmp_dir):
        run('rm -rf %s' % (remote_script_tmp_dir))
    run('mkdir -p %s' % (remote_script_tmp_dir))
    
    # upload zip file to remote and then unzip
    with lcd(perf_test_script_zip_tmp_dir):
        put(perf_test_script_zip_name, remote_script_tmp_dir)
    
    with cd(remote_script_tmp_dir):
        # unzip - o / Users / xieyanyang / work / learning / autodeploy / src / autodeploy / core_vex / vex.zip - d / tmp / deploy - core - vex
        run('unzip -o %s -d %s' % (perf_test_script_zip_name, remote_script_tmp_dir))
        run('rm -rf %s/%s' % (remote_script_tmp_dir, perf_test_script_zip_name))
    
    # start load test
    with cd(remote_script_tmp_dir + package_path):
        run('nohup python %s > %s' % (load_test_script_file_name, remote_script_tmp_dir + package_path + '/vod_test.log'), shell=False, pty=True, quiet=False)

if __name__ == '__main__':              
    execute(kill_vod_test)
    # execute(rm_vod_test_log)
    # execute(execute_load_test)
    
