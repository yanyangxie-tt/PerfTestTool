# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

'''
Distributed load test script
'''
from fabric.context_managers import cd, lcd
from fabric.contrib.files import exists
from fabric.decorators import task, parallel, roles
from fabric.operations import run, put, local
from fabric.tasks import execute
from init_script_env import *

here = os.path.dirname(os.path.realpath(__file__))
project_dir, package_path = here.split('src')
project_source_dir = project_dir + os.sep + 'src'

@task
@parallel
@roles(perf_test_machine_group)
def stop_perf_test():
    fab_util.fab_shutdown_service(load_test_sigle_process_script_file)

@task
@parallel
@roles(perf_test_machine_group)
def rm_perf_test_log():
    run('rm -rf %s' % (perf_test_remote_result_dir), pty=False)

@task
@parallel
@roles(perf_test_machine_group)
def start_perf_test():
    zip_perf_test_script()
    upload_test_script()
    with cd(perf_test_remote_script_dir + package_path):
        # run('nohup python %s > %s' % (load_test_multiple_script_file_name, perf_test_remote_script_dir + package_path + '/perf_test.log'), shell=False, pty=True, quiet=False)
        run('nohup python %s >/dev/null 2>&1' % (load_test_multiple_script_file_name), shell=False, pty=True, quiet=False)

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

config_dict = read_configurations()
set_fabric_env(config_dict)

if __name__ == '__main__':              
    execute(stop_perf_test)
    execute(rm_perf_test_log)
    execute(start_perf_test)
    
