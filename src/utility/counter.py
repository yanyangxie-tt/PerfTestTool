# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

class Metric():
    '''Metric is to record the total number which meet the special range, such as [100, 200]'''
    
    def __init__(self, metric_range):
        '''
        @param metric_range: such as [100, 200]
        '''
        if type(metric_range) not in [list, tuple] or len(metric_range) != 2:
            raise Exception('Metric range must be like [1, 200], please check')
        
        self.metric_range = metric_range
        self.metric_min, self.metric_max = metric_range
        self.count = 0
    
    def increase(self, number):
        '''increase 1 if number is in this metric range'''
        if number > self.metric_min and number <= self.metric_max:
            self.count += 1
            return self.count
        else:
            return False
    
    def __repr__(self):
        return '%6s-%6s:%s' % (self.metric_range[0], self.metric_range[1], self.count)

class Counter(object):
    '''Counter is to count the total number which is meeting special metric range.'''
    def __init__(self, counter_list, name='', limitless=100000):
        '''
        @param counter_list: boundary of metric range, such as [0, 1000, 3000, 6000]
        @param name: counter name
        @param limitless: setup a max number of one metric. If counted number is larger than the limitless, not count it 
        '''
        self.name = name
        self.counter_in_total = 0
        self.counter_metric_dict = {}
        self.max = limitless
        self._init_metrics(counter_list, limitless)
        
    
    def _init_metrics(self, counter_list, limitless):
        '''Generate metric list by counter list'''
        if type(counter_list) not in [list, tuple]:
            raise Exception('counter list must be a list or tuple')

        for n in counter_list:
            if type(n) is not int or n < 0:
                raise Exception('number in counter list must be a integer value and >=0')
        
        counter_list = list(set(counter_list))
        counter_list.sort()
        range_list = [[counter_list[i], counter_list[i + 1]] for i in range(0, len(counter_list)) if i < len(counter_list) - 1]
        
        # append [counter_list[-1], int_limitless]
        if counter_list[-1] < limitless:
            range_list.append([counter_list[-1], limitless])
        else:
            self.max = limitless
        
        # append [0, counter_list[0]]
        if counter_list[0] != 0:
            range_list.insert(0, [0, counter_list[0]])
        
        
        self.metric_list = [Metric(m_range) for m_range in range_list]
    
    def increment(self, number):
        '''increase 1 if number meets one metric range'''
        if number > self.max:
            return False
            # return Exception('number %s is not in counter range')
        else:
            self.counter_in_total += 1
        
        for metric in self.metric_list:
            if metric.increase(number):
                break
    
    def dump(self):
        '''dump metric string'''
        return [str(metric) for metric in self.metric_list]
    
    def get_metrics(self):
        return self.metric_list
    
    def get_total_count(self):
        return self.counter_in_total
    
    def __repr__(self):
        return self.dump()

if __name__ == '__main__':
    c = Counter(['1000', '2000', '3000', '6000', ])
    c.increment(200)
    c.increment(1200)
    c.increment(1000)
    c.increment(10000000)
    infos = c.dump()
    for i in infos:
        print i
    
    print c.get_total_count()
