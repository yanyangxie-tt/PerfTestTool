# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import os
import time

import requests

from perf.test.model import manifest
from perf.test.model.vex_perf_test import VEXPerfTestBase
from utility import time_util, manifest_util


class VODPerfTest(VEXPerfTestBase):
    def __init__(self, config_file, current_process_number=0, **kwargs):
        '''
        @param config_file: configuration file, must be a properties file
        @param log_file: log file absolute path
        '''
        super(VODPerfTest, self).__init__(config_file, current_process_index=current_process_number, **kwargs)
    
    def set_compontent_private_default_value(self):
        self._set_attr('test_type_options', ['VOD_T6', 'OTHER:VOD'])
        self._set_attr('index_url_format', 'http://mm.vod.comcast.net/%s/king/index.m3u8?ProviderId=%s&AssetId=abcd1234567890123456&StreamType=%s&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00')
    
    # linear vod, cdvr do_index is the same
    def do_index(self, task):
        try:
            self.logger.debug('Execute index: %s' % (str(task)))
            
            fake_response_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'index-fake-response.txt'
            if os.path.exists(fake_response_file):
                response = requests.get('http://www.baidu.com')
                f = open(fake_response_file)
                response_text = f.read()
                used_time = 201
            else:
                response, used_time = self._get_vex_response(task, tag='Index')
                response_text = response.text
            
            if response is None:
                self._increment_counter(self.index_counter, self.index_lock, response_time=used_time, is_error=True)
                return
            elif response.status_code != 200:
                self.logger.warn('Failed to index request. Status code:%s, message=%s, task:%s' % (response.status_code, response_text, task))
                self._increment_counter(self.index_counter, self.index_lock, response_time=used_time, is_error=True)
                return
            
            self._increment_counter(self.index_counter, self.index_lock, response_time=used_time, is_error=False)
            self.logger.debug('Index response for task[%s]:\n%s' % (task, response_text,))
            
            bitrate_url_list = manifest_util.get_bitrate_urls(response_text, self.test_bitrate_request_number)
            for i, bitrate_url in enumerate(bitrate_url_list):
                b_task = task.clone()
                delta_milliseconds = self.test_bitrate_serial_time * (i + 1) if self.test_bitrate_serial else self.test_bitrate_serial_time
                start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_milliseconds=delta_milliseconds)
                b_task.set_bitrate_url(bitrate_url)
                b_task.set_start_date(start_date)
                self.logger.debug('Schedule bitrate request. task:%s' % (b_task))
                self.task_consumer_sched.add_date_job(self.do_bitrate, start_date, args=(b_task,))
        except Exception, e:
            print e
            self._increment_counter(self.index_counter, self.index_lock, response_time=0, is_error=True)
            self.logger.error('Failed to index request.', e)
    
    # linear vod, cdvr do_bitrate, get_response之前都一样，可以提取公共的。接下来的check，linear和cdvr继续发送bitrate请求这里单独写    
    def do_bitrate(self, task):
        try:
            self.logger.debug('Execute bitrate: %s' % (str(task)))
            
            fake_response_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'index-fake-response.txt'
            if os.path.exists(fake_response_file):
                response = requests.get('http://www.baidu.com')
                f = open(fake_response_file)
                response_text = f.read()  # 如果不check或者不发psn, 无需读取response
                used_time = 200
            else:
                response, used_time = self._get_vex_response(task, tag='Bitrate')
                response_text = response.text
                
            if response is None:
                self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=used_time, is_error=True)
                return
            elif response.status_code != 200:
                self.logger.warn('Failed to bitrate request. Status code:%s, message=%s, task:%s' % (response.status_code, response_text, task))
                self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=used_time, is_error=True)
                return
            else:
                self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=used_time, is_error=False)
            
            if not self.send_psn_message and not self._has_attr('client_response_check_when_running'):
                return
            
            self.logger.debug('Bitrate response for task[%s]:\n%s' % (task, response_text,))
            # manifest parser
            m = manifest.VODManifestPaser(response_text, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_')
            if self._has_attr('client_response_check_when_running'):
                # 如何计算ad的位置？pre和post的
                # client.response.ad.pre.roll.ts.number=10
                # client.response.ad.post.roll.ts.number=10
                # client.response.ad.mid.roll.ts.number=10
                # client.response.ad.mid.roll.position=75,150,225
                
                expected_ad_position_list = []
                error_message = m.check(self.client_response_media_sequence, self.client_response_content_segment_number,
                                        self.client_response_endlist_tag, self.client_response_drm_tag, expected_ad_position_list,
                                        self.client_response_ad_pre_roll_ts_number, self.client_response_ad_mid_roll_ts_number, self.client_response_ad_post_roll_ts_number,
                                        )
                if error_message is not None:
                    self.logger.error(error_message)
                    self.error_record_queue.put(error_message, False, 2)
            
            # @todo
            # send_psn
                
        except Exception, e:
            self._increment_counter(self.bitrate_counter, self.bitrate_lock, response_time=0, is_error=True)
            self.logger.error('Failed to bitrate request.', e)
    
    def check_response(self, bitrate_manifest, task):
        m = manifest.ManifestPaser(bitrate_manifest, task.get_bitrate_url(), psn_tag=self.psn_tag, ad_tag=self.client_response_ad_tag, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_')
        m.parse()
        if m.has_asset_id is False:
            self.logger.error('Not found same asset id from manifest. url:%s, manifest:%s' % (task.get_bitrate_url(), bitrate_manifest))
            # 记录error
            return
    
    
    '''
    def check_response_data(item, t_manifest, primary_ts_number, ad_ts_number, first_ad_position, media_sequence_number, asset_id, has_asset_id, t_time):
        try:
            error_message_list = []
            
            if not has_asset_id:
                error_message_list.append('\n\tAsset ID in bit rate response unmatched. Index asset id: %s, bit rate manifest: %s' % (str(asset_id), str(t_manifest)))
            
            if media_sequence is not None:
                # check media sequence
                if media_sequence_number is None:
                    error_message_list.append('\n\tMedia sequence is None, not the same as checked media sequence %s' % (str(media_sequence)))
                elif int(media_sequence) != int(media_sequence_number):
                    error_message_list.append('\n\tMedia sequence is %s, not the same as checked media sequence %s' % (str(media_sequence_number), str(media_sequence)))
            
            hasSAP = item[0].find("HasSAP=true") > 0
            logger.info("xie: hasSAP: %s" % hasSAP)
            logger.info("xie: item[0]: %s" % (item[0]))
            logger.info("xie: is_sap_not_insert_ad and hasSAP: %s" % (is_sap_not_insert_ad and hasSAP))
            
            if is_sap_not_insert_ad and hasSAP:
                # while is_sap_not_insert_ad==True and content is SAP, not insert any ad in it
                if int(vod_content_length) != primary_ts_number:
                    error_message_list.append('\n\tTotal primary ts size is %s, not the same as fixed recording length %s' % (primary_ts_number, vod_content_length))
                
                if t_manifest.find(end_list_tag) < 0:
                    error_message_list.append('\n\tNot found end list tag %s' % (end_list_tag))
                
                if drm_tag is not None and t_manifest.find(drm_tag) < 0:
                    error_message_list.append('\n\tNot found drm info %s' % (drm_tag))
                
                if ad_ts_number != 0 :
                    error_message_list.append('\n\tAD TS number in SAP should be 0, current is %s' % (ad_ts_number))
                    
                
            elif mid_roll_ad_positions is not None and mid_roll_ad_ts_number is not None and vod_content_length is not None:
                if int(vod_content_length) != primary_ts_number:
                    error_message_list.append('\n\tTotal primary ts size is %s, not the same as fixed recording length %s' % (primary_ts_number, vod_content_length))
                
                if t_manifest.find(end_list_tag) < 0:
                    error_message_list.append('\n\tNot found end list tag %s' % (end_list_tag))
                    
                if drm_tag is not None and t_manifest.find(drm_tag) < 0:
                    error_message_list.append('\n\tNot found drm info %s' % (drm_tag))
                
                # need calculate the first ad position to confirm the total ad number
                expected_mid_roll_ad_number = len(mid_roll_ad_positions.split(',')) * mid_roll_ad_ts_number
                expected_ad_number = pre_roll_ad_ts_number + expected_mid_roll_ad_number + post_roll_ad_ts_number
                
                # expected_ad_number = ad_ts_batch_size * (1 + vod_content_length/primary_ts_batch_size if vod_content_length%primary_ts_batch_size!=0 else vod_content_length/primary_ts_batch_size)
                if expected_ad_number != ad_ts_number:
                    logger.error("\n\tTotal AD size is %s, not the same as expected %s ADs." % (ad_ts_number, expected_ad_number))
                    error_message_list.append('\n\tTotal AD size is %s, not the same as expected %s ADs.' % (ad_ts_number, expected_ad_number))
                elif item[4].find('iframe') > 0 and t_manifest.find('ad_iframe') < 0:
                    logger.error("\n\tAD content is not a iframe AD")
                    error_message_list.append("\n\tAD content is not a iframe AD")
                elif item[4].find('audio') > 0 and (t_manifest.find('audio') < 0):
                    logger.error("\n\tAD content is not a audio AD")
                    error_message_list.append("\n\tAD content is not a audio AD")
                    
            if error_message_list is not None and len(error_message_list) > 0:
                error_message_list = ['%s. Validation failed. IP:%s, URL:%s' % (time_util.datetime_2_string(t_time), item[1], item[0])] + error_message_list + ['\n', ]
                error_messages = string.join(error_message_list)
                logger.error(error_messages)
                logger.error(t_manifest)
                error_analysis_report_queue.put(error_messages, timeout=10)
        except:
            exce_info = 'Line %s: %s' % ((sys.exc_info()[2]).tb_lineno, sys.exc_info()[1])
            logger.error("Failed to check response. Exception: %s." % (exce_info))
            logger.error("Manifest is: %s" % (t_manifest))
    '''
            
    def _get_vex_response(self, task, tag='Index'):
        response, used_time = None, 0
        try:
            response, used_time = self.get_response(task, self.test_client_request_timeout)
        except Exception, e:
            self.logger.error('Failed to do %s task. %s. %s' % (tag, task, e), exc_info=0)
            
            mtries = self.test_client_request_retry_count
            retry_count = 1
            while mtries > 1:
                time.sleep(self.test_client_request_retry_delay)
                try:
                    self.logger.debug('Retry index, %s time. task:[%s]' % (retry_count, task))
                    response, used_time = self.get_response(task, self.test_client_request_timeout)
                    return response
                except Exception, e:
                    self.logger.error('Retry index failed, %s time. task:[%s]' % (retry_count, task))
                    mtries -= 1
        return response, used_time

    def task_generater(self):
        while True:
            if self.task_queue.full():
                self.logger.debug('Task queue is meet the max number %s, sleep 5 seconds' % (self.task_queue.maxsize))
                time.sleep(5)
                continue
            self.task_queue.put_nowait(self._generate_task())

    def dispatch_task(self):
        self.logger.debug('Start to dispatch task')
        if self.current_processs_concurrent_request_number == 0:
            self.logger.warn('Current request number for this process(%s) is 0, exit.' % (self.current_process_number))
            exit(0)
        
        if hasattr(self, 'test_warmup_period_minute'):
            warm_up_second_list = self._generate_warm_up_list()
            # generate warm-up rate
            if len(warm_up_second_list) > 0:
                self.logger.debug('Warm-up process, warm-up %s minute, warm rate %s' % (self.test_warmup_period_minute, [i for i in warm_up_second_list if i / 60 == 0]))
                # Fetch tasks by the number of warm_up_second_list, and then add it to task consumer(task sched)
                for task_number in warm_up_second_list:
                    self.logger.info('Warm-up stage: Put %s task into task queue' % (task_number))
                    index = 0
                    while index < task_number:
                        task = self.task_queue.get(True, timeout=10)
                        start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=3)
                        task.set_start_date(start_date)
                        self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
                        index += 1
                    time.sleep(1)
        
        self.logger.debug('Start to do performance with max current request %s of this process' % (self.current_processs_concurrent_request_number))
        self.dispatch_task_sched.add_interval_job(self._fetch_task_and_add_to_consumer, seconds=1)
    
    def _fetch_task_and_add_to_consumer(self):
        # Fetch task from task queue, and add it to task consumer
        self.logger.debug('Put %s tasks into task schedule.' % (self.current_processs_concurrent_request_number))
        for i in range(0, self.current_processs_concurrent_request_number):
            try:
                task = self.task_queue.get(True, 6)
                start_date = time_util.get_datetime_after(time_util.get_local_now(), delta_seconds=1)
                task.set_start_date(start_date)
                self.task_consumer_sched.add_date_job(self.do_index, start_date, args=(task,))
            except Exception, e:
                self.logger.error('Failed to fetch task from task queue', e)
    
    def _generate_warm_up_list(self):
        warm_up_period_minute = self._has_attr('test_warmup_period_minute')
        if not warm_up_period_minute:
            return []
        
        warm_up_second_list = []
        if warm_up_period_minute and warm_up_period_minute > 1:
            warm_up_minute_list = self._generate_warm_up_request_list(self.current_processs_concurrent_request_number, warm_up_period_minute)
            self.logger.info('Warm-up period is %s minute, warm-up list is:%s' % (warm_up_period_minute, warm_up_minute_list))
        else:
            self.logger.debug('Warm-up period is not set or its value <1, not do warm up')
            return []
        
        # to VOD, export warm up rate by seconds
        for t in warm_up_minute_list:
            for i in range(0, 1 * 60):
                warm_up_second_list.append(t)
        
        return warm_up_second_list

if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    
    config_file = here + os.sep + 'config.properties'
    golden_config_file = here + os.sep + 'config-golden.properties'
    
    v = VODPerfTest(config_file, golden_config_file=golden_config_file)
    v.run()
