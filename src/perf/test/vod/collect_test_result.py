# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from init_script_env import *
from perf.test.model.vex_distribute import DistributeEnv
from utility import fab_util

class ResultCollection(DistributeEnv):
    def __init__(self, config_file, **kwargs):
        '''@param config_file: configuration file, must be a properties file'''
        super(ResultCollection, self).__init__(config_file, **kwargs)
        self.project_dir, self.package_path = here.split('src')
        self.project_source_dir = self.project_dir + os.sep + 'src'
        fab_util.set_roles(perf_test_machine_group, self.test_machine_hosts,)
