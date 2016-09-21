# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import string

from fabric.context_managers import settings, cd
from fabric.operations import local, run
from fabric.state import env
from fabric.tasks import execute

from init_script_env import *
from perf.test.model.vex_distribute import DistributeEnv
from utility import fab_util, vex_util

# local dir for merge report
local_vex_tmp_dir = '/tmp/'
local_tmp_dir = local_vex_tmp_dir + 'report-merge' # 将来改成local_vex_tmp_report_dir
local_zip_dir = local_tmp_dir + os.sep + 'remote_zip_dir'
local_delta_report_dir = local_tmp_dir + os.sep + 'report-info'
local_traced_response_dir = local_tmp_dir + os.sep + 'traced_response'
local_error_file_dir = local_tmp_dir + os.sep + 'error-info'

class ResultCollection(DistributeEnv):
    def __init__(self, config_file, **kwargs):
        '''@param config_file: configuration file, must be a properties file'''
        super(ResultCollection, self).__init__(config_file, **kwargs)
        self.set_env()
    
    def set_env(self):    
        fab_util.set_roles(perf_test_machine_group, self.test_machine_hosts,)
        
        self.project_dir, self.package_path = here.split('src')
        self.project_source_dir = self.project_dir + os.sep + 'src'
        self.perf_test_remote_result_dir = getattr(self, 'test_result_report_dir') if hasattr(self, 'test_result_report_dir') else ''
        self.perf_test_name = getattr(self, 'test_case_name') if hasattr(self, 'test_case_name') else perf_test_remote_result_default_dir
        self.perf_test_remote_result_dir = vex_util.get_test_result_tmp_dir(self.perf_test_remote_result_dir, self.perf_test_name)
        print self.perf_test_remote_result_dir
    
    def collect_vod_test_result_from_remote(self):
        local_host_zip_dir = local_zip_dir + os.sep + string.replace(env.host, '.', '-')
        local('mkdir -p %s' % (local_host_zip_dir))
        
        tmp_zip_file = 'tmp-vex-load-test-result.zip'
        with cd(local_vex_tmp_dir):
            run('rm -rf %s' % (tmp_zip_file))
            
            report_files_reg = '%s/*/%s' % (self.perf_test_remote_result_dir, '1234')
            print report_files_reg
        
        '''
        
        # zip all the result file and download to local
        with cd('/vex-tmp'):
            run('rm -rf %s' % (tmp_zip_file))
            report_files_reg = '%s/*/%s' % (remote_result_dir, constants.report_file)
            errors_files_reg = '%s/*/%s' % (remote_result_dir, constants.error_response_dir)
            # traced_files_reg = '%s/*/%s' % (remote_result_dir, constants.trace_file_dir)
            
            traced_files_time_reg = time_util.generate_time_reg_list(collected_start_time_hour_before_now, collected_end_time_hour_before_now)
            traced_files_reg_list = ['%s/*/%s/*%s*' % (remote_result_dir, constants.trace_file_dir, time_reg) for time_reg in traced_files_time_reg]
            traced_files_reg = string.join(traced_files_reg_list, ' ')
            print 'Zip result file in remote server using command \'zip -r %s %s %s %s\'' % (tmp_zip_file, report_files_reg, traced_files_reg, errors_files_reg)
            run('zip -r %s %s %s %s' % (tmp_zip_file, report_files_reg, traced_files_reg, errors_files_reg))
            
            print 'Start to download results info from remote %s to local folder %s' % (tmp_zip_file, local_host_zip_dir)
            get(tmp_zip_file, local_host_zip_dir)
            print 'Finish to download delta report from remote server'
            
        with lcd(local_host_zip_dir):
            local('unzip %s' % (tmp_zip_file))
        '''
        
    def run(self):
        print 1
        with settings(parallel=True, roles=[perf_test_machine_group, ]):
            execute(self.collect_vod_test_result_from_remote)

if __name__ == '__main__':
    collect = ResultCollection(config_file, golden_config_file=golden_config_file)
    collect.run()