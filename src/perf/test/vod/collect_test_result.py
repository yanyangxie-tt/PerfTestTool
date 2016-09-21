# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import datetime

from init_script_env import *
from perf.test.model.vex_counter import VEXMetricCounter
from perf.test.model.vex_result_collection import ResultCollection
from utility import file_util

class VODResultAnalyzer(ResultCollection):
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        super(VODResultAnalyzer, self).__init__(config_file, collect_traced_data, collected_result_before_now, **kwargs)
        self.init_vex_counter()
        
        self.report_file_dir = here + os.sep + 'reports'
        self.summary_file_name = 'summary-report-%s.txt' % (datetime.datetime.now().strftime("%Y-%m-%d"))
        self.index_bitrate_report_sep = 'Bitrate'
     
    def init_vex_counter(self, **kwargs):
        # initial response time metric object for both index and bitrate 
        default_counters = [0, 1000, 3000, 6000, 12000]
        generate_counter = lambda att, default_value: getattr(self, att) if self._has_attr(att) else default_value
        setattr(self, 'index_counter', generate_counter('index_response_counter', default_counters))
        setattr(self, 'bitrate_counter', generate_counter('bitrate_response_counter', default_counters))   
        
    '''
    Export a final test report to local file
    @param total_report_info_dir: local dir of report files. Should be the same as local_delta_report_dir
    @param exported_report_file_dir: exported report file dir
    @param exported_report_file_name: exported report file name
    '''
    def export_summarized_report_data(self):
        # 遍历local_zip_dir, 找到所report file的文件全路径
        file_list = file_util.get_matched_file_list(self.local_zip_dir, self.test_result_report_file)
        print file_list
        
        # 使用map的方式，对全部的找到的文件进行数据归集。在VEXMetricCounter里保存数据
        summarized_report_file = '/tmp/vex_test_result_dir/54-169-146-58/test-result-0/load-test-report.txt'
        self.parse_one_summarized_report_file(summarized_report_file)
        
        # 对map的结果进行合并
        
        # 输出测试结果
    
    def parse_one_summarized_report_file(self, summarized_report_file):
        with open(summarized_report_file) as f:
            summarized_content = f.read()
        
        index_summarized_content, bitrate_summarized_content = summarized_content.split(self.index_bitrate_report_sep)  
        index_counter = VEXMetricCounter(self.index_counter)
        index_counter.parse(index_summarized_content)
        print index_counter.dump_counter_info(index_counter.counter_period)
        
    
    def summary_data_parser(self, summary_file):
        index_metric = VEXMetricCounter()
        bitrate_metric = VEXMetricCounter()
    
    def analysis(self):
        #self.collect()
        self.export_summarized_report_data()

if __name__ == '__main__':
    analyzer = VODResultAnalyzer(config_file, golden_config_file=golden_config_file)
    analyzer.analysis()