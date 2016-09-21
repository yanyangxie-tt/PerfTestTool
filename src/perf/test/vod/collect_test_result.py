# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import datetime

from init_script_env import *
from perf.test.model.vex_result_collection import ResultCollection
from utility import file_util


class VODResultAnalyzer(ResultCollection):
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        super(VODResultAnalyzer, self).__init__(config_file, collect_traced_data, collected_result_before_now, **kwargs)
        
        self.report_file_dir = here + os.sep + 'reports'
        self.summary_file_name = 'summary-report-%s.txt' % (datetime.datetime.now().strftime("%Y-%m-%d"))
            
     
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
        
        # 使用map的方式，对全部的找到的文件进行数据归集。在一个类里保存数据
        
        # 对map的结果进行合并
        
        # 输出测试结果
        
    
    def analysis(self):
        #self.collect()
        self.export_summarized_report_data()
    

if __name__ == '__main__':
    analyzer = VODResultAnalyzer(config_file, golden_config_file=golden_config_file)
    analyzer.analysis()