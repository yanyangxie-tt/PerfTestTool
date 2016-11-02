import datetime
import os

from perf.model.vex_counter import VEXMetricCounter
from perf.result.result_collection import ResultCollection
from utility import file_util, time_util

class ResultAnalyzer(ResultCollection):
    def __init__(self, config_file, report_dir, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        # collect_traced_data: whether to download traced bitrate response data to local to do result analysis
        super(ResultAnalyzer, self).__init__(config_file, collect_traced_data, collected_result_before_now, **kwargs)
        self.report_dir = report_dir
        self.index_report_content = ''
        self.bitrate_report_content = ''
        self.error_report_content = ''
        
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
        
        self.summary_file_name = 'summary-report-%s.txt' % (datetime.datetime.now().strftime("%Y-%m-%d"))
        self.error_file_name = 'error-report-%s.txt' % (datetime.datetime.now().strftime("%Y-%m-%d"))
        
        self._set_attr('db_vex_result_table', 'perf_test', False)
        self._set_attr('db_vex_result_store_enable', False, False)
        self._set_attr('test_case_server_instance_number', 2, False)
    
    def export_summarized_report_data(self):
        '''Export test summarized report to local file'''
        summarized_report_file_list = file_util.get_matched_file_list(self.local_zip_dir, self.test_result_report_file)
        counters = map(self._parse_summarized_report_file, summarized_report_file_list)
        index_counter_list = [counter[0] for counter in counters]
        bitrate_counter_list = [counter[1] for counter in counters]

        final_index_report_counter = self._merge_vex_count_list(index_counter_list)
        final_bitrate_report_counter = self._merge_vex_count_list(bitrate_counter_list)
        
        if final_index_report_counter is not None and final_bitrate_report_counter is not None:
            report_content = ''
            self.index_report_content = final_index_report_counter.dump_counter_info(final_index_report_counter.counter_period, tag=self.index_summary_tag, export_concurrent_number=self.export_concurrent_number)
            self.bitrate_report_content = final_bitrate_report_counter.dump_counter_info(final_bitrate_report_counter.counter_period, tag=self.bitrate_summary_tag, export_concurrent_number=self.export_concurrent_number)
            report_content = self.index_report_content + '\n' + self.bitrate_report_content
            
            print report_content
            print 'Export summarized report to %s' % (self.report_dir + os.sep + self.summary_file_name)
            file_util.write_file(self.report_dir, self.summary_file_name, report_content, is_delete=True)
    
    def export_error_data(self):
        error_report_file_list = file_util.get_matched_file_list(self.local_zip_dir, self.test_result_report_error_file + '-.*\d+$')
        for error_report_file in error_report_file_list:
            with open(error_report_file) as f:
                self.error_report_content += f.read()
        
        # to linear and cdvr, need merge
        self.error_report_content = self.reorganize_error_data(self.error_report_content)
        
        if self.error_report_content != '':
            print 'Export error report to %s' % (self.report_dir + os.sep + self.error_file_name)
            file_util.write_file(self.report_dir, self.error_file_name, self.error_report_content, is_delete=True)
    
    def reorganize_error_data(self, error_content):
        return error_content
    
    def export_parsed_traced_data(self):
        pass
    
    def export_report_to_db(self):
        if self.db_vex_result_store_enable is False or self.connector is None:
            return
        
        try:
            current_date = time_util.get_current_day_start_date()
            self.connector.execute("select * from " + self.db_vex_result_table + " where project_name='%s' and project_version='%s' and test_type='%s' and test_date='%s'" \
                                   %(self.project_name, self.project_version, self.test_case_type, current_date))
            
            p_result = self.connector.find_one()
            if p_result is not None:
                p_id = p_result['id']
                self.connector.execute("delete from " + self.db_vex_result_table + " where id='%s'" %(p_id))
            else:
                self.connector.execute("select id from " + self.db_vex_result_table)
                ids = [d['id'] for d in self.connector.find_all()]
                ids.sort()
                p_id = ids[-1] + 1
            
            sql = "insert into " + self.db_vex_result_table + " values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            value = []
            value.append(p_id)
            value.append(self.project_name)
            value.append(self.project_version)
            value.append(self.test_case_type)
            value.append(current_date)
            value.append(str(self.parameters))
            value.append(self.index_report_content)
            value.append(self.bitrate_report_content)
            value.append(self.error_report_content)
            value.append(self.test_case_server_instance_number)
            value_list = [tuple(value),]
            self.connector.execute_with_values(sql, value_list)
            print 'Perf test result has been saved into DB.'
        except Exception, e:
            print 'Failed to save test result into DB.' + e
    
    def _merge_vex_count_list(self, counter_list):
        if counter_list is None or len(counter_list) == 0:
            return None
        
        if len(counter_list) == 1:
            return counter_list[0]
        
        self.total_count = 0
        self.succeed_total_count = 0
        self.error_total_count = 0
        self.response_time_sum = 0
        self.response_error_total_count = 0
        
        merged_key_list = ['total_count', 'succeed_total_count', 'error_total_count', 'response_time_sum',
                           'response_error_total_count', 'metric_list']
        final_report_counter = counter_list[0]
        for counter in counter_list[1:]:
            for key, value in counter.__dict__.items():
                if key not in merged_key_list:
                    continue
                
                if key == 'metric_list':
                    for i, metric in enumerate(value):
                        # final_report_counter.metric_list[i] is a Metric instance
                        final_report_counter.metric_list[i].count += metric.count
                else:
                    setattr(final_report_counter, key, getattr(final_report_counter, key) + value)
        return final_report_counter
    
    def _parse_summarized_report_file(self, summarized_report_file):
        with open(summarized_report_file) as f:
            summarized_content = f.read()
        
        index_summarized_content, bitrate_summarized_content = summarized_content.split(self.bitrate_summary_tag)  
        index_counter = VEXMetricCounter(self.index_counter)
        index_counter.parse(index_summarized_content)
        
        bit_rate_counter = VEXMetricCounter(self.bitrate_counter)
        bit_rate_counter.parse(bitrate_summarized_content)
        return [index_counter, bit_rate_counter]
    
    def analysis(self, collect_from_remote=True):
        if collect_from_remote:
            self.collect()
        self.export_summarized_report_data()
        self.export_error_data()
        self.export_report_to_db()
        if self.collect_traced_data is True:
            self.export_parsed_traced_data()
