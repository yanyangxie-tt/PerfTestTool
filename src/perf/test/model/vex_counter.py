import copy
from utility.counter import MetricCounter

class VEXMetricCounter(MetricCounter):
    def __init__(self, counter_list, name='', limitless=12000):
        super(VEXMetricCounter, self).__init__(counter_list, name, limitless)
        self.delta_metric_list = copy.deepcopy(self.metric_list)
        
        self.total_count = 0
        self.succeed_total_count = 0
        self.error_total_count = 0
        self.sum_number = 0
        
        self.delta_total_count = 0
        self.delta_succeed_total_count = 0
        self.delta_error_total_count = 0
        self.delta_sum_number = 0
    
    def increment_error(self):
        self.error_total_count += 1
        self.delta_error_total_count += 1
        
        self.total_count += 1
        self.delta_total_count += 1
    
    def increment(self, number):
        '''increase 1 if number meets one metric range'''
        if number > self.max:
            return
        
        for metric in self.metric_list:
            if metric.increase(number):
                break
        
        for metric in self.delta_metric_list:
            if metric.increase(number):
                break    
        
        # to vex, number is response time
        self.total_count += 1
        self.succeed_total_count += 1
        self.sum_number += number
        
        self.delta_total_count += 1
        self.delta_succeed_total_count += 1
        self.delta_sum_number += number
        
    def dump_delta_metric(self):
        '''dump delta metric string'''
        return [str(metric) for metric in self.delta_metric_list]
    
    def clear_delta_metric(self):
        
        self.delta_total_count = 0
        self.delta_succeed_total_count = 0
        self.delta_error_total_count = 0
        self.delta_sum_number = 0
        
        for metric in self.delta_metric_list:
            metric.count = 0
    
    def get_summary(self):
        return [self.total_count, self.succeed_total_count, self.error_total_count, self.sum_number, self.metric_list]
    
    def get_delta_summary(self):
        return [self.delta_total_count, self.delta_succeed_total_count, self.delta_error_total_count, self.delta_sum_number, self.delta_metric_list]
    
    def dump_counter_info(self, counter_period, delta=False, tag='Response summary',):
        total_count, succeed_total_count, error_total_count, sum_number, metric_list = self.get_delta_summary() if delta else self.get_summary()
        
        if total_count == 0:
            return ''
        
        summary = ''
        summary += '%-21s:%s\n' % (tag, '')
        summary += '%2s%-19s:%-4s seconds\n' % ('', 'Total time', counter_period)
        summary += '%2s%-19s:%s\n' % ('', 'Total   requests   ', total_count)
        summary += '%2s%-19s:%s\n' % ('', 'Succeed requests   ', succeed_total_count)
        summary += '%2s%-19s:%s\n' % ('', 'Failure requests   ', error_total_count)
        summary += '%2s%-19s:%.2f%%\n' % ('', 'Succeed rate', 100 * (float(succeed_total_count) / total_count))
        summary += '%2s%-19s:%s\n' % ('', 'Average response', sum_number / succeed_total_count if succeed_total_count != 0 else 0)
        summary += '%2s%-19s:%s\n' % ('', 'Metric  details', '')
        
        for metric in metric_list:
            summary += '%4s%-17s:%-4s milliseconds\n' % ('', str(metric.metric_range[0]) + '-' + str(metric.metric_range[0]), metric.count)
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
    infos = c.dump_delta_metric()
    # for i in infos:
    #    print i
    
    # print c.get_summary()
    # print c.get_delta_summary()
    # print c
    
    # c.clear_delta_metric()
    # print c.get_delta_summary()
    print c.dump_counter_info(10)

    
