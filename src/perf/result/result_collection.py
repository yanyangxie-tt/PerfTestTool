# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import string

from fabric.context_managers import cd, lcd, settings
from fabric.operations import local, run, get
from fabric.state import env
from fabric.tasks import execute

from perf.model.vex_distribute import DistributeEnv
from utility import fab_util, vex_util, time_util

class ResultCollection(DistributeEnv):
    # collection test result from remote test machine
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param collect_traced_data: whether to collect traced data from remote test machine 
        @param collected_result_before_now: if collect traced data, how long the file should be analyzed. Time unit is hour
        '''
        super(ResultCollection, self).__init__(config_file, **kwargs)
        
        self.collect_traced_data = collect_traced_data
        self.collected_result_before_now=collected_result_before_now
        self.perf_test_machine_group = 'perf_test_machines'
        
        self.vex_tmp_dir = '/tmp'
        self.local_zip_dir = self.vex_tmp_dir + os.sep + 'vex_test_result_dir'
        
        self.setup_env()
    
    def setup_env(self):
        if not hasattr(self, 'test_result_report_dir'):
            print 'test result report dir is required.'
            exit(1)
        
        fab_util.set_roles(self.perf_test_machine_group, self.test_machine_hosts,)
        
        self.perf_test_remote_result_dir = getattr(self, 'test_result_report_dir')
        self.perf_test_name = getattr(self, 'test_case_name') if hasattr(self, 'test_case_name') else ''
        self.perf_test_remote_result_dir = vex_util.get_test_result_tmp_dir(self.perf_test_remote_result_dir, self.perf_test_name)
        
        self.report_file_reg = '*/%s' % (self.test_result_report_file)
        self.traced_file_dir_reg = '*/%s' % (self.test_result_report_traced_dir)
        self.error_file_dir_reg = '*/%s' % (self.test_result_report_error_dir)
        
        self.traced_files_reg = self.get_traced_files_reg(self.traced_file_dir_reg, self.test_result_report_traced_file, self.collected_result_before_now)
        self.error_files_reg = self.get_traced_files_reg(self.error_file_dir_reg, self.test_result_report_error_file, self.collected_result_before_now)
    
    def collect_vod_test_result_from_remote(self):
        print 'Start to download files from remote'
        tmp_zip_file_name = 'tmp-vex-load-test-result.zip'
        local_host_zip_dir = self.local_zip_dir + os.sep + string.replace(env.host, '.', '-')
        local('rm -rf %s/*' %(local_host_zip_dir))
        local('mkdir -p %s' % (local_host_zip_dir))
        
        with cd(self.perf_test_remote_result_dir):
            tmp_zip_file = self.vex_tmp_dir +os.sep + 'tmp-vex-load-test-result.zip'
            run('rm -rf %s' % (tmp_zip_file))
            
            #print 'Start to zip expected file in remote, please wait...'
            if self.collect_traced_data is True:
                print 'zip result file in remote test machine using command \'zip -r %s %s %s %s\'' % (tmp_zip_file, self.report_file_reg, self.traced_files_reg, self.error_files_reg)
                run('zip -r %s %s %s %s' % (tmp_zip_file, self.report_file_reg, self.traced_files_reg, self.error_files_reg), quiet=True)
            else:
                print 'zip result file in remote test machine using command \'zip -r %s %s %s\'' % (tmp_zip_file, self.report_file_reg, self.error_files_reg)
                run('zip -r %s %s %s' % (tmp_zip_file, self.report_file_reg, self.error_files_reg), quiet=True)
            
            print 'Start to download results info from remote %s to local folder %s' % (tmp_zip_file, local_host_zip_dir)
            get(tmp_zip_file, local_host_zip_dir)
            print 'Finish to download delta report from remote server'
            run('rm -rf %s' % (tmp_zip_file))
        
        with lcd(local_host_zip_dir):
            local('unzip -o %s' % (tmp_zip_file_name))
    
    def get_traced_files_reg(self, file_dir, file_name, collected_result_before_now):
        files_time_reg = time_util.generate_time_reg_list(end_time_hour_before_now=collected_result_before_now)
        files_reg_list = ['%s/%s-%s*' % (file_dir, file_name, time_reg) for time_reg in files_time_reg]
        return string.join(files_reg_list, ' ')
    
    def collect(self):
        local('rm -rf %s/*' %(self.local_zip_dir))
        with settings(parallel=True, roles=[self.perf_test_machine_group, ]):
            execute(self.collect_vod_test_result_from_remote)

