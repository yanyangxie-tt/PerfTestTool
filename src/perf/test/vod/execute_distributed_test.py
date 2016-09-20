# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

'''
Distributed load test script
'''
from fabric.context_managers import settings, cd, lcd
from fabric.contrib.files import exists
from fabric.operations import run, put, local
from fabric.tasks import execute

from init_script_env import *
from perf.test.model.configuration import Configurations
from utility import fab_util, vex_util

class DistributePerfTest(Configurations):
    def __init__(self, config_file, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        '''
        super(DistributePerfTest, self).__init__(config_file, **kwargs)
        self.set_fabric_env()
        self.project_dir, self.package_path = here.split('src')
        self.project_source_dir = self.project_dir + os.sep + 'src'
    
    def set_fabric_env(self):
        self._set_attr('test_machine_port', '22')
        self._set_attr('test_machine_username', 'root')
        
        if not hasattr(self, 'test_machine_pubkey') and not hasattr(self, 'test_virtual_machine_password'):
            print 'pubkey and password must have one'
            exit(1)
        
        if not hasattr(self, 'test_machine_hosts'):
            print 'Test machine hosts is required'
            exit(1)
        elif type(self.test_machine_hosts) is str:
            self.test_machine_hosts = [self.test_machine_hosts, ]
        
        if hasattr(self, 'test_machine_username'): fab_util.set_user(self.test_machine_username)
        if hasattr(self, 'test_machine_port'): fab_util.set_port(self.test_machine_port)
        if hasattr(self, 'test_machine_pubkey'): fab_util.set_key_file(self.test_machine_pubkey)
        if hasattr(self, 'test_virtual_machine_password'): fab_util.set_password(self.test_virtual_machine_password)
        fab_util.set_roles(perf_test_machine_group, self.test_machine_hosts,)
    
    def rm_perf_test_log(self):
        perf_test_remote_result_dir = getattr(self, 'test_result_report_dir') if hasattr(self, 'test_result_report_dir') else ''
        perf_test_name = getattr(self, 'test_case_name') if hasattr(self, 'test_case_name') else perf_test_remote_result_default_dir
        perf_test_remote_result_dir = vex_util.get_test_result_tmp_dir(perf_test_remote_result_dir, perf_test_name)
        run('rm -rf %s' % (perf_test_remote_result_dir), pty=False)
    
    def stop_perf_test(self):
        fab_util.fab_shutdown_service(load_test_sigle_process_script_file)
    
    def start_perf_test(self):
        self.zip_perf_test_script()
        self.upload_test_script()
        
        with cd(perf_test_remote_script_dir + self.package_path):
            run('nohup python %s >/dev/null 2>&1' % (load_test_multiple_script_file_name), shell=False, pty=True, quiet=False)
    
    def restart_perf_test(self):
        execute(self.stop_perf_test)
        execute(self.rm_perf_test_log)
        execute(self.start_perf_test)
    
    def execute_task(self, method):
        with settings(parallel=True, roles=[perf_test_machine_group, ]):
            execute(getattr(self, method))
    
    def upload_test_script(self):
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
    
    def zip_perf_test_script(self):
        with lcd(self.project_source_dir):
            if os.path.exists(perf_test_script_zip_file_name):
                os.remove(perf_test_script_zip_file_name)
            
            zip_command = 'zip -r %s perf utility' % (perf_test_script_zip_file_name)
            local(zip_command)

if __name__ == '__main__':
    distribute_test = DistributePerfTest(config_file, golden_config_file=golden_config_file)
    task_name = sys.argv[1] if len(sys.argv) > 1 else 'restart_perf_test'
    distribute_test.execute_task(task_name)
    
    #distribute_test.execute_task('stop_perf_test')
    #distribute_test.execute_task('rm_perf_test_log')
    #distribute_test.execute_task('start_perf_test')
