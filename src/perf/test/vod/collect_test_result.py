# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import datetime

from init_script_env import *
from perf.model.vex_counter import VEXMetricCounter
from perf.result.result_analyzer import ResultAnalyzer
from utility import file_util


class VODResultAnalyzer(ResultAnalyzer):
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        report_dir = here + os.sep + 'reports'
        
        #collect_traced_data: whether to download traced bitrate response data to local to do result analysis
        super(VODResultAnalyzer, self).__init__(config_file, report_dir, collect_traced_data, collected_result_before_now, **kwargs)

if __name__ == '__main__':
    analyzer = VODResultAnalyzer(config_file, golden_config_file=golden_config_file)
    analyzer.analysis()