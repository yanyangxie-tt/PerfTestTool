# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from init_script_env import *
from perf.result.result_analyzer import ResultAnalyzer

class VODResultAnalyzer(ResultAnalyzer):
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        self.export_concurrent_number = True
        report_dir = here + os.sep + 'reports'
        super(VODResultAnalyzer, self).__init__(config_file, report_dir, collect_traced_data, collected_result_before_now, **kwargs)

if __name__ == '__main__':
    analyzer = VODResultAnalyzer(config_file, golden_config_file=golden_config_file)
    analyzer.analysis(True)