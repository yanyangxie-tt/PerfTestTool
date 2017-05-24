# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com

import os
import re

class ManifestPaser(object):
    def __init__(self, manifest, request_url, psn_tag=None, ad_tag=None, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_', provider_tag = 'ProviderId'):
        self.manifest = manifest
        self.request_url = request_url
        self.psn_tag = psn_tag
        self.ad_tag = ad_tag
        self.sequence_tag = sequence_tag
        self.asset_id_tag = asset_id_tag
        self.provider_tag = provider_tag
        
        self.ad_ts_number = 0
        self.ad_pre_number = 0
        self.ad_post_number = 0
        self.ad_mid_number = 0
        self.ad_mid_position_list = []
        self.ad_url_list=[]
        self.sequence_number = 0
        self.has_asset_id = False
        self.entertainment_ts_number = 0
        self.psn_tracking_position_id_dict = {}
    
    def parse(self):
        self.asset_id = self.extract_asset_id(self.request_url)
        if self.asset_id is None:
            self.has_asset_id = False
        
        manifest_list = self.manifest.split('\n')
        entertainment_ts_index, tmp_index = 0, 0
        for line in manifest_list:
            line = line.strip()
            if line == '':
                continue
            
            if line.find(self.sequence_tag) >= 0:
                self.sequence_number = int(line.rsplit(':')[-1].strip('\r'))
                continue
            
            if self.has_asset_id is not True and line.find(self.asset_id) > 0:
                self.has_asset_id = True
            
            if self.psn_tag is not None and line.find(self.psn_tag) > -1:
                trackingId = self.extract_psn_tracking_id(line)
                if trackingId != '':
                    self.psn_tracking_position_id_dict[entertainment_ts_index] = trackingId    
            elif line.find('.ts') > 0:
                if line.find(self.ad_tag) > -1:
                    self.ad_ts_number += 1
                    self.ad_url_list.append(line)
                    
                    if entertainment_ts_index < 1:
                        # not found entertainment ts, should be preroll ad
                        self.ad_pre_number += 1
                    else:
                        # mid or post roll ad. Record ad ts number and started postion 
                        # 暂时不知道，这个是midroll还是postroll的ad。先假定其是postroll的
                        tmp_index = entertainment_ts_index
                        self.ad_post_number += 1
                elif line.find(self.asset_id_tag) > -1:
                    self.entertainment_ts_number += 1
                    entertainment_ts_index += 1
                    
                    if self.ad_post_number > 0:
                        # 当在ad后又遇见entertainment的ts，证明之前记录的是mid roll的ad。此时记录midroll的postion和number。同时将postroll的清零
                        self.ad_mid_position_list.append(tmp_index)
                        self.ad_mid_number += self.ad_post_number
                        self.ad_post_number = 0

    def extract_psn_tracking_id(self, content):
        '''Get PSN tracking id'''
        p = r'\w*\W*ID=(.*),DURATION[\.\n]*'
        psn_info = re.findall(p, content)
        
        if psn_info is not None and len(psn_info) > 0:
            return psn_info[0]            

    '''
    def extract_asset_id(self, url):
        flag = '/.*(%s.*)/' % (self.asset_id_tag)
        p = r'\w*\W*%s[\.\n]*' % (flag)
        t_info = re.findall(p, url)
    
        if t_info is not None and len(t_info) > 0:
            return t_info[0].split('/')[0]
        else:
            return None
    '''

    def extract_asset_id(self, url):
        #re.findall(r'.*ProviderId=(.*?)\&.*', url)
        p = r'.*%s=(.*?)\&.*' %(self.provider_tag)
        t_info = re.findall(p, url)
    
        if t_info is not None and len(t_info) > 0:
            return t_info[0].split('/')[0]
        else:
            return None

class LinearManifestChecker(ManifestPaser):
    def __init__(self, manifest, request_url, psn_tag=None, ad_tag=None, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_'):
        super(LinearManifestChecker, self).__init__(manifest, request_url, psn_tag, ad_tag, sequence_tag, asset_id_tag)
        self.parse()
        self.ad_data_transform()
    
    def ad_data_transform(self):
        self.ad_in_first_postion = True if self.ad_pre_number > 0 else False

class CdvrManifestChecker(ManifestPaser):
    def __init__(self, manifest, request_url, psn_tag=None, ad_tag=None, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_'):
        super(CdvrManifestChecker, self).__init__(manifest, request_url, psn_tag, ad_tag, sequence_tag, asset_id_tag)
        self.parse()
        self.generate_ad_position_list()
        
    def generate_ad_position_list(self):
        if self.ad_pre_number > 0:
            self.ad_mid_position_list.insert(0, 0)
        
        if self.ad_post_number > 0:
            self.ad_mid_position_list.append(self.entertainment_ts_number)

class VODManifestChecker(ManifestPaser):
    def __init__(self, manifest, request_url, psn_tag=None, ad_tag=None, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_'):
        super(VODManifestChecker, self).__init__(manifest, request_url, psn_tag, ad_tag, sequence_tag, asset_id_tag)
        self.parse()
        self.error = None
    
    def check(self, media_sequence_number, entertainment_ts_number, end_list_tag, drm_tag,
              ad_mid_position_list, ad_pre_number, ad_mid_number, ad_post_number,
              iframe_tag='IsIFrame=true', ad_iframe_tag='ad_iframe', audio_tag='IsAudio=true', ad_audio_tag='ad_audio'):
        
        message = None
        while True:
            if self.has_asset_id is not True:
                message = 'Not found same asset id from manifest. url:%s' % (self.request_url)
                break
            elif self.sequence_number != media_sequence_number:
                message = 'Manifest media sequence number is %s, not the same as expected number %s' % (self.sequence_number, media_sequence_number)
                break
            elif self.entertainment_ts_number != entertainment_ts_number:
                message = 'Manifest entertainment ts number is %s, not the same as expected number %s' % (self.entertainment_ts_number, entertainment_ts_number)
                break
            elif self.manifest.find(end_list_tag) < 0:
                message = 'Manifest has not end list tag %s' % (end_list_tag)
                break
            elif self.manifest.find(drm_tag) < 0:
                message = 'Manifest has not drm tag %s' % (drm_tag)
                break
            elif self.ad_pre_number != ad_pre_number:
                message = 'Manifest ad pre-roll number is %s, not the same as expected number %s' % (self.ad_pre_number, ad_pre_number)
                break
            elif self.ad_mid_position_list != ad_mid_position_list:
                message = 'Manifest ad mid-roll positions is %s, not the same as expected %s' % (self.ad_mid_position_list, ad_mid_position_list)
                break
            elif self.ad_mid_number != ad_mid_number:
                message = 'Manifest ad mid-roll position is right, but number is %s, not the same as expected number %s' % (self.ad_mid_number, ad_mid_number)
                break
            elif self.ad_post_number != ad_post_number:
                message = 'Manifest ad post-roll number is %s, not the same as expected number %s' % (self.ad_post_number, ad_post_number)
                break
            elif self.request_url.find(iframe_tag) > 0 and self.manifest.find(ad_iframe_tag) < 0:
                message = 'Manifest has not ad iframe tag %s, but %s is found in url %s' % (ad_iframe_tag, iframe_tag, self.request_url)
                break
            elif self.request_url.find(audio_tag) > 0 and self.manifest.find(ad_audio_tag) < 0:
                message = 'Manifest has not ad audio tag \'%s\', but %s is found in url %s' % (ad_audio_tag, audio_tag, self.request_url)
                break
            else:
                break
        self.error = message
        return self.error

if __name__ == '__main__':    
    request_url = 'http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/99999999/vod_test_7975_med_3.m3u8?&IndexName=index.m3u8&BitRelLength=176&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050300&MinBW=2050100&IsIFrame=false&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC'
    with open(os.path.dirname(os.path.realpath(__file__)) + '/../vod/fake/bitrate-fake-response.txt') as f:
        manifest = f.read()
    
    checker = VODManifestChecker(manifest, request_url, psn_tag=None, ad_tag='ad', asset_id_tag='vod_')
    print checker.check(18, 900, '#EXT-X-ENDLIST', 'EXT-X-FAXS-CM', [225, 450, 675], 10, 30, 10)
