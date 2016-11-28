import copy
import threading

class LinearBitrateResult():
    '''Save one parsed bitrate response info'''
    
    def __init__(self, task, request_time, sequence_number, entertainment_number, ad_number, ad_url_list):
        '''
        @param task: linear request task
        @param request_time: bitrate request time(datetime)
        @param sequence_number: sequence number
        @param entertainment_number: total entertainment ts number
        @param ad_number: total ad ts number
        @param ad_url_list: ad url list
        '''
        
        self.task = task
        self.request_time = request_time
        self.ad_number = ad_number
        self.ad_url_list = ad_url_list
        self.sequence_number = sequence_number
        self.entertainment_number = entertainment_number
        self.exist_ad = True if self.ad_number > 0 else False
    
    def __repr__(self):
        return '%s[%s]:sequence_number:%s, entertainment number:%-2s, ad number:%-2s' \
            % (self.task.get_client_ip(), self.request_time, self.sequence_number, self.entertainment_number, self.ad_number)

class LinearBitrateResultTrace():
    '''Traced one client bitrate requests and response, and then check the traced response'''
    def __init__(self, task, ad_insertion_frequency='200/20', content_segment_time=2, sequence_increase_request_number=2):
        '''
        @param task: linear request task
        @param ad_insertion_frequency: same as the ad_insertion_frequency in mock origin
        @param content_segment_time: time of one ts
        @param sequence_increase_request_number: how often that segment number must be increased.
                    Take t6linear for example, vex will do manifest expansion every 2 second and client call vex every second, 
                    so at least two request will make segment number increase by 1.
        '''
        
        self.lock = threading.RLock()
        self.task = task
        self.bitrate_url = task.get_bitrate_url()
        self.bitrate_result_list = []
        self.ad_insertion_frequency = ad_insertion_frequency
        self.content_segment_time = content_segment_time
        self.ad_number_in_complete_cycle = int(ad_insertion_frequency.split('/')[1])
        self.entertainment_number_in_complete_cycle = int(ad_insertion_frequency.split('/')[0])
        self.sequence_increase_request_number = sequence_increase_request_number
        self.time_format = '%Y-%m-%d %H:%M:%S'
        
        self.error_list = []
        
    def add_bitrate_result(self, result):
        # store one bitrate result of one client
        if not isinstance(result, LinearBitrateResult):
            return
        
        with self.lock:
            self.bitrate_result_list.append(result)
    
    def check(self, logger=None):
        if logger is not None:
            self.logger = logger
        
        if len(self.bitrate_result_list) == 0:
            return

        # while checking, test client is also running, and bitrate result is still be inserted into the traced list
        # so need to copy the current static traced datas and do data analysis using those static traced datas
        with self.lock:
            bitrate_result_list = copy.copy(self.bitrate_result_list)
            self.bitrate_result_list = []
        
        # 1st, separate bitrate url list to multiple data segment
        self.log_debug('Bitrate list in checked list:\n%s' % (bitrate_result_list))
        bitrate_group_list, has_ad_in_total = self.group_result(bitrate_result_list)
        self.log_debug('Checked list has ad:%s, Grouped result list is:\n%s' % (has_ad_in_total, bitrate_group_list))
        
        # 2st, if separated list(group list) has only one element, then it maybe has no ad. So need check whether its request number is larger than expected
        # if no ad, then record the error
        if len(bitrate_group_list) == 1 and has_ad_in_total is False:
            if len(bitrate_group_list[0]) > self.entertainment_number_in_complete_cycle:
                message = 'No ad found in one ad-insertion cycle. Time window:%s~%s.' \
                    % (bitrate_group_list[0][0].request_time.strftime(self.time_format), bitrate_result_list[-1].request_time.strftime(self.time_format),)
                
                #message = 'No ad found in one ad-insertion cycle. Entertainment number is %s, larger than %s. Time window: %s~%s.' \
                #    % (len(bitrate_group_list[0]), self.entertainment_number_in_complete_cycle, bitrate_group_list[0][0].request_time.strftime(self.time_format), bitrate_result_list[-1].request_time.strftime(self.time_format),)
                self.record_error(message)
                return
        
        # to the latest element, not sure whether it is one completely ad-insertion cycle, so not check it but re-add it into system bitrate result traced list
        latest_bitrate_group = bitrate_group_list.pop(-1)
        with self.lock:
            self.bitrate_result_list = latest_bitrate_group + self.bitrate_result_list
        
        self.log_debug('Grouped result list(Removed latest) is:\n%s' % (bitrate_group_list))
        for bitrate_group in bitrate_group_list:
            self.analysis_bitrate_group(bitrate_group)
    
    def group_result(self, bitrate_result_list):
        '''
        Separate traced bitrate result list to multiple segments which is one completely ad-insertion cycle, such as 300/30 
        Separate rule is that one manifest has not ad, but previous one has ad. then here is the traced list separator
        Each data segment must start with (manifest without ad), and end with (manifest with ad)
        For example. 0 means one manifest without ad, 1 means one manifest with ad.
        [0,1,1,1,1,0,0,0,1,1,1,0,0,0,1,1,1,0,0]
            --> [[0, 1, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0,0]]
        
        [1,1,0,0,0,1,1,1,0,0,0,1,1,1,0,0]
            --> [[1, 1], [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0,0]]
        '''
        if len(bitrate_result_list) == 0:
            return []
        
        has_ad_in_total = False
        total_groups = []
        groups = []
        
        for i, bitrate_result in enumerate(bitrate_result_list):
            if i == 0:
                groups.append(bitrate_result)
            elif bitrate_result_list[i - 1].exist_ad is True and bitrate_result.exist_ad is not True:
                # one manifest has not ad, but previous has ad
                total_groups.append(groups)
                groups = []
                groups.append(bitrate_result)
                has_ad_in_total = True
            else:
                groups.append(bitrate_result)
        
        if len(groups) > 0:
            total_groups.append(groups)
        
        return total_groups, has_ad_in_total

    def analysis_bitrate_group(self, bitrate_result_list):
        if len(bitrate_result_list) == 0:
            return
        
        # if first element in bitrate_result_list is ad, then it is one completely ad-insertion cycle, ignore it
        if bitrate_result_list[0].exist_ad is True:
            return
        
        ad_url_set = set([])
        entertainment_request_size = 0
        for i, bitrate_result in enumerate(bitrate_result_list):
            if i > self.sequence_increase_request_number:
                pre_bitrate_result = bitrate_result_list[i - self.sequence_increase_request_number]
                if bitrate_result.sequence_number <= pre_bitrate_result.sequence_number:
                    message = 'Sequence number is not increased. %s:%s, %s:%s' \
                            % (pre_bitrate_result.request_time, pre_bitrate_result.sequence_number, bitrate_result.request_time, bitrate_result.sequence_number,)
                    self.record_error(message)
                
            if bitrate_result.ad_number > 0:
                ad_url_set = ad_url_set.union(set(bitrate_result.ad_url_list))
            else:
                entertainment_request_size += 1
        
        if entertainment_request_size > self.entertainment_number_in_complete_cycle:
            message = 'No ad found in one ad-insertion cycle. Time window: %s~%s.' \
                    % (bitrate_result_list[0].request_time.strftime(self.time_format), bitrate_result_list[-1].request_time.strftime(self.time_format),)
            
            #message = 'No ad found in one ad-insertion cycle. Entertainment number is %s, larger than %s. Time window: %s~%s.' \
            #        % (entertainment_request_size, self.entertainment_number_in_complete_cycle, bitrate_result_list[0].request_time, bitrate_result_list[-1].request_time,)
            self.record_error(message)
        
        if len(ad_url_set) != self.ad_number_in_complete_cycle:
            message = 'AD number is not as expected. Ad number:%s, expected ad number: %s. Time window: %s~%s. ' \
                    % (len(ad_url_set), self.ad_number_in_complete_cycle, bitrate_result_list[0].request_time.strftime(self.time_format), bitrate_result_list[-1].request_time.strftime(self.time_format),)
            self.record_error(message)
    
    def log_debug(self, message):
        if self.logger: self.logger.debug('%s:%s' % (self.task.get_client_ip(), message))
    
    def record_error(self, message):
        self.error_list.append(message)
        if self.logger: self.logger.error('%s:%s' % (self.task.get_client_ip(), message))
