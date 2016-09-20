# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import copy
from utility.counter import MetricCounter

class VEXMetricCounter(MetricCounter):
    def __init__(self, counter_list, name='', limitless=12000):
        super(VEXMetricCounter, self).__init__(counter_list, name, limitless)
        self.delta_metric_list = copy.deepcopy(self.metric_list)
        
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
    
    def dump_counter_info(self, counter_period, delta=False, tag='Response summary',):
        total_count, succeed_total_count, error_total_count, response_time_sum, response_error_count, metric_list = self.get_delta_summary() if delta else self.get_summary()
        
        if total_count == 0:
            return ''
        
        summary = ''
        summary += '%-24s\n' % (tag)
        summary += '%2s%-22s: %-4s seconds\n' % ('', 'Perf Test Duration', counter_period)
        summary += '%2s%-22s: %s\n' % ('', 'Request In Total', total_count)
        summary += '%2s%-22s: %s\n' % ('', 'Request Succeed', succeed_total_count)
        summary += '%2s%-22s: %s\n' % ('', 'Request Failure', error_total_count)
        summary += '%2s%-22s: %.2f%%\n' % ('', 'Request Succeed Rate', 100 * (float(succeed_total_count) / total_count))
        summary += '%2s%-22s: %s\n' % ('', 'Response Average Time', response_time_sum / succeed_total_count if succeed_total_count != 0 else 0)
        summary += '%2s%-22s: %s\n' % ('', 'Response Failure', response_error_count)
        summary += '%2s%-22s\n' % ('', 'Response Time Distribution')
        
        for metric in metric_list:
            summary += '%6s%-10s milliseconds: %s\n' % ('', str(metric.metric_range[0]) + '-' + str(metric.metric_range[1]), metric.count)
        return summary
    
    def parser(self, summary_info):
        pass
    
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
    print c.dump_counter_info(10)
