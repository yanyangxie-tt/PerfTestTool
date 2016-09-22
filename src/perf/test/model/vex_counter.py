# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import copy

from utility.counter import MetricCounter


class VEXMetricCounter(MetricCounter):
    def __init__(self, counter_list, name='', limitless=12000):
        super(VEXMetricCounter, self).__init__(counter_list, name, limitless)
        self.delta_metric_list = copy.deepcopy(self.metric_list)
        self.init_counter()
        self.set_vex_counter_name()
    
    def init_counter(self):
        self.total_count = 0
        self.succeed_total_count = 0
        self.error_total_count = 0
        self.response_time_sum = 0
        self.response_error_total_count = 0
        
        self.delta_total_count = 0
        self.delta_succeed_total_count = 0
        self.delta_error_total_count = 0
        self.delta_response_sum = 0
        self.delta_response_error_total_count = 0
    
    def set_vex_counter_name(self):
        self.test_duration_tag= 'Test Duration (second)'
        self.test_concurrent_number = 'Request concurrent'
        self.total_request_tag = 'Request In Total'
        self.succeed_request_tag = 'Request Succeed'
        self.succeed_rate_tag = 'Request Succeed Rate'
        self.failed_request_tag = 'Request Failure'
        self.average_response_tag = 'Response Average Time'
        self.failed_response_tag = 'Response Failure'
        self.response_time_distribution = 'Response Time Distribution'
        
        self.millisecond = 'millisecond'
    
    def increment_error(self):
        self.error_total_count += 1
        self.delta_error_total_count += 1
        
        self.total_count += 1
        self.delta_total_count += 1
        
    def increment_error_response(self):
        self.response_error_total_count += 1
        self.delta_response_error_total_count += 1
    
    def increment(self, response_time):
        '''increase 1 if response_time meets one metric range'''
        if response_time > self.max:
            return
        
        for metric in self.metric_list:
            if metric.increase(response_time):
                break
        
        for metric in self.delta_metric_list:
            if metric.increase(response_time):
                break    
        
        # to vex, response_time is response time
        self.total_count += 1
        self.succeed_total_count += 1
        self.response_time_sum += response_time
        
        self.delta_total_count += 1
        self.delta_succeed_total_count += 1
        self.delta_response_sum += response_time
        
    def dump_delta_metric(self):
        '''dump delta metric string'''
        return [str(metric) for metric in self.delta_metric_list]
    
    def clear_delta_metric(self):
        self.delta_total_count = 0
        self.delta_succeed_total_count = 0
        self.delta_error_total_count = 0
        self.delta_response_sum = 0
        self.delta_response_error_total_count = 0
        
        for metric in self.delta_metric_list:
            metric.count = 0
    
    def get_summary(self):
        return [self.total_count, self.succeed_total_count, self.error_total_count, self.response_time_sum, self.response_error_total_count, self.metric_list]
    
    def get_delta_summary(self):
        return [self.delta_total_count, self.delta_succeed_total_count, self.delta_error_total_count, self.delta_response_sum, self.delta_response_error_total_count, self.delta_metric_list]
    
    def dump_counter_info(self, counter_period, delta=False, tag='Response summary', is_vod=True):
        total_count, succeed_total_count, error_total_count, response_time_sum, response_error_count, metric_list = self.get_delta_summary() if delta else self.get_summary()
        
        if total_count == 0:
            return ''
        
        summary = ''
        summary += '%-24s\n' % (tag)
        summary += '%2s%-22s: %-4s\n' % ('', self.test_duration_tag, counter_period)
        if is_vod is True: 
            summary += '%2s%-22s: %-4s\n' % ('', self.test_concurrent_number, total_count/int(counter_period))
        summary += '%2s%-22s: %s\n' % ('', self.total_request_tag, total_count)
        summary += '%2s%-22s: %s\n' % ('', self.succeed_request_tag, succeed_total_count)
        summary += '%2s%-22s: %s\n' % ('', self.failed_request_tag, error_total_count)
        summary += '%2s%-22s: %.2f%%\n' % ('', self.succeed_rate_tag, 100 * (float(succeed_total_count) / total_count))
        summary += '%2s%-22s: %s\n' % ('', self.average_response_tag, response_time_sum / succeed_total_count if succeed_total_count != 0 else 0)
        
        if is_vod is True:
            summary += '%2s%-22s: %s\n' % ('', self.failed_response_tag, response_error_count)
        summary += '%2s%-22s\n' % ('', self.response_time_distribution)
        
        for metric in metric_list:
            summary += '%6s%-10s %s: %s\n' % ('', str(metric.metric_range[0]) + metric.metric_sep + str(metric.metric_range[1]),self.millisecond, metric.count)
        return summary
    
    def parse(self, summary_info):
        summary_counter_info, resposne_metric_info = summary_info.split(self.response_time_distribution)
        for line in summary_counter_info.split('\n'):
            if line.find(self.test_duration_tag) > 0:
                self.counter_period = line.split(':')[1].strip()
                continue
            elif line.find(self.total_request_tag) > 0:
                self.total_count = int(line.split(':')[1].strip())
                continue
            elif line.find(self.succeed_request_tag) > 0 and line.find(self.succeed_rate_tag) < 0:
                self.succeed_total_count = int(line.split(':')[1].strip())
                continue
            elif line.find(self.failed_request_tag) > 0:
                self.error_total_count = int(line.split(':')[1].strip())
                continue
            elif line.find(self.average_response_tag) > 0:
                self.average_response_time = int(line.split(':')[1].strip())
                self.response_time_sum = self.average_response_time * int(self.succeed_total_count)
                continue
            elif line.find(self.failed_response_tag) > 0:
                self.response_error_total_count = int(line.split(':')[1].strip())
                continue
            
        resposne_metric_dict = {}
        for metric in resposne_metric_info.split('\n'):
            metric =  metric.strip()
            if metric.find(':') < 0:
                continue
            
            metric_range, value =  metric.split(':')
            metric_range = metric_range.replace(self.millisecond,'').strip()
            resposne_metric_dict[metric_range] = int(value.strip())
        
        for metric in self.metric_list:
            metric_string = metric.get_metric_string()
            if resposne_metric_dict.has_key(metric_string):
                metric.count = resposne_metric_dict.get(metric_string)
        #print self.dump_counter_info(self.counter_period)
    
    def __repr__(self):
        return str(self.__dict__)

if __name__ == '__main__':
    c = VEXMetricCounter([1000, 2000, 3000, 6000, ])
    c.increment(200)
    c.increment(1200)
    c.increment(1000)
    c.increment_error()
    c.increment_error()
    c.increment_error_response()
    infos = c.dump_delta_metric()
    
    
    content = c.dump_counter_info(10)
    print content
    
    c.parse(content)
    print c
    
    print VEXMetricCounter.get_vex_counter_name()
