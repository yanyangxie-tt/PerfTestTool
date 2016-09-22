# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import datetime

from init_script_env import *
from perf.test.model.vex_counter import VEXMetricCounter
from perf.test.model.vex_result_collection import ResultCollection
from utility import file_util

class VODResultAnalyzer(ResultCollection):
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        #collect_traced_data: whether to download traced bitrate response data to local to do result analysis
        super(VODResultAnalyzer, self).__init__(config_file, collect_traced_data, collected_result_before_now, **kwargs)
        self.init_vex_counter()
        self.init_report_env()
     
    def init_vex_counter(self, **kwargs):
        # initial response time metric object for both index and bitrate 
        default_counters = [0, 1000, 3000, 6000, 12000]
        generate_counter = lambda att, default_value: getattr(self, att) if self._has_attr(att) else default_value
        setattr(self, 'index_counter', generate_counter('index_response_counter', default_counters))
        setattr(self, 'bitrate_counter', generate_counter('bitrate_response_counter', default_counters))
    
    def init_report_env(self):
        self._set_attr('index_summary_tag', 'Index response summary', False)
        self._set_attr('bitrate_summary_tag', 'Bitrate response summary', False)
        
        self.report_file_dir = here + os.sep + 'reports'
        self.summary_file_name = 'summary-report-%s.txt' % (datetime.datetime.now().strftime("%Y-%m-%d"))
    
    def export_summarized_report_data(self):
        '''Export a test summarized report to local file'''
        summarized_report_file_list = file_util.get_matched_file_list(self.local_zip_dir, self.test_result_report_file)
        counters = map(self.parse_summarized_report_file, summarized_report_file_list)
        index_counter_list = [counter[0] for counter in counters]
        bitrate_counter_list = [counter[1] for counter in counters]

        final_index_report_counter = self.merge_vex_count_list(index_counter_list)
        final_bitrate_report_counter = self.merge_vex_count_list(bitrate_counter_list)
        
        report_content = final_index_report_counter.dump_counter_info(final_index_report_counter.counter_period, tag=self.index_summary_tag,)
        report_content += '\n' + final_bitrate_report_counter.dump_counter_info(final_bitrate_report_counter.counter_period, tag=self.bitrate_summary_tag,)
        print report_content
        print 'Export summarized report to %s' %(self.report_file_dir + os.sep + self.summary_file_name)
        file_util.write_file(self.report_file_dir, self.summary_file_name, report_content, is_delete=True)
    
    def merge_vex_count_list(self, counter_list, ):
        if counter_list is None or len(counter_list) == 0:
            return None
        
        if len(counter_list) == 1:
            return counter_list[0]
        
        self.total_count = 0
        self.succeed_total_count = 0
        self.error_total_count = 0
        self.response_time_sum = 0
        self.response_error_total_count = 0
        
        merged_key_list = ['total_count','succeed_total_count','error_total_count','response_time_sum', 
                           'response_error_total_count', 'metric_list']
        final_report_counter = counter_list[0]
        for counter in counter_list[1:]:
            for key, value in counter.__dict__.items():
                if key not in merged_key_list:
                    continue
                
                if key == 'metric_list':
                    for i, metric in enumerate(value):
                        #final_report_counter.metric_list[i] is a Metric instance
                        final_report_counter.metric_list[i].count += metric.count
                else:
                    setattr(final_report_counter, key, getattr(final_report_counter, key) + value)
        return final_report_counter
    
    def parse_summarized_report_file(self, summarized_report_file):
        with open(summarized_report_file) as f:
            summarized_content = f.read()
        
        index_summarized_content, bitrate_summarized_content = summarized_content.split(self.bitrate_summary_tag)  
        index_counter = VEXMetricCounter(self.index_counter)
        index_counter.parse(index_summarized_content)
        
        bit_rate_counter = VEXMetricCounter(self.bitrate_counter)
        bit_rate_counter.parse(bitrate_summarized_content)
        return [index_counter, bit_rate_counter]
    
    def analysis(self):
        self.collect()
        self.export_summarized_report_data()

if __name__ == '__main__':
    analyzer = VODResultAnalyzer(config_file, golden_config_file=golden_config_file)
    analyzer.analysis()