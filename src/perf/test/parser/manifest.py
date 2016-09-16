# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import re

from utility import psn_util


class ManifestPaser(object):
    def __init__(self, manifest, request_url, psn_tag=None, ad_tag=None, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_',):
        self.manifest = manifest
        self.request_url = request_url
        self.psn_tag = psn_tag
        self.ad_tag = ad_tag
        self.sequence_tag = sequence_tag
        self.asset_id_tag = asset_id_tag
        
        self.ad_ts_number = 0
        self.ad_pre_number = 0
        self.ad_post_number = 0
        self.ad_mid_number = 0
        self.ad_mid_position_list = []
        self.sequence_number = 0
        self.has_asset_id = False
        self.entertainment_ts_number = 0
        self.psn_tracking_position_id_dict = {}
    
    def parse(self):
        self.asset_id = self.extract_asset_id(self.request_url)
        if self.asset_id is None:
            return
        self.asset_id = 'e'
        
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
                pass
                trackingId = psn_util.get_psn_tracking_id(line)
                if trackingId != '':
                    self.psn_tracking_position_id_dict[entertainment_ts_index] = trackingId    
            elif line.find('.ts') > 0:
                if line.find(self.ad_tag) > -1:
                    self.ad_ts_number += 1
                    
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
                
    
    def extract_asset_id(self, url):
        flag = '/(%s.*)/' % (self.asset_id_tag)
        p = r'\w*\W*%s[\.\n]*' % (flag)
        t_info = re.findall(p, url)
    
        if t_info is not None and len(t_info) > 0:
            return t_info[0].split('/')[0]
        else:
            return None

class VODManifestChecker(ManifestPaser):
    def __init__(self, manifest, request_url, psn_tag=None, ad_tag=None, sequence_tag='#EXT-X-MEDIA-SEQUENCE', asset_id_tag='vod_'):
        super(VODManifestChecker, self).__init__(manifest, request_url, psn_tag, ad_tag, sequence_tag, asset_id_tag)
        self.parse()
        self.error = None
    
    def check(self, media_sequence_number, entertainment_ts_number, end_list_tag, drm_tag,
              ad_mid_position_list, pre_ad_number, mid_ad_number, post_ad_number,
              iframe_tag='iframe', ad_iframe_tag='ad_iframe', audio_tag='audio', ad_audio_tag='audio'):
        
        while True:
            if self.has_asset_id is not True:
                message = 'Not found same asset id from manifest. url:%s, manifest:%s' % (self.request_url, self.manifest)
                break
        
            if self.sequence_number != media_sequence_number:
                message = 'Manifest media sequence number is %s, not the same as expected number %s' % (self.sequence_number, media_sequence_number)
                break
            
            if self.entertainment_ts_number != entertainment_ts_number:
                message = 'Manifest entertainment ts number is %s, not the same as expected number %s' % (self.entertainment_ts_number, entertainment_ts_number)
                break
            
            if self.manifest.find('end_list_tag') < 0:
                message = 'Manifest has not end list tag %s' % (end_list_tag)
                break
            
            if self.manifest.find('drm_tag') < 0:
                message = 'Manifest has not drm tag %s' % (drm_tag)
                break
            
            if self.ad_mid_position_list != ad_mid_position_list:
                message = 'Manifest ad positions is %s, not the same as expected %s' % (self.ad_mid_position_list, ad_mid_position_list)
                break
            
            if self.pre_ad_number != pre_ad_number:
                message = 'Manifest ad preroll number number is %s, not the same as expected number %s' % (self.pre_ad_number, pre_ad_number)
                break
            
            if self.mid_ad_number != mid_ad_number:
                message = 'Manifest ad midroll number number is %s, not the same as expected number %s' % (self.mid_ad_number, mid_ad_number)
                break
            
            if self.post_ad_number != post_ad_number:
                message = 'Manifest ad postroll number number is %s, not the same as expected number %s' % (self.post_ad_number, post_ad_number)
                break
            
            if self.request_url.find(iframe_tag) > 0 and self.manifest.find(ad_iframe_tag) < 0:
                message = 'Manifest has not ad iframe tag %s, which exists in url %s' % (self.ad_iframe_tag, self.request_url)
                break
            
            if self.request_url.find(audio_tag) > 0 and self.manifest.find(ad_audio_tag) < 0:
                message = 'Manifest has not ad audio tag %s, which exists in url %s' % (self.ad_audio_tag, self.request_url)
                break
        self.error = message
        return self.error

if __name__ == '__main__':    
    request_url = 'www.baidu.com/vod_test_1/index.m3u8'
    manifest = '''
    ad_1.ts\n
    vod_1.ts\n
    vod_2.ts\n
    ad_2.ts\n
    vod_3.ts\n
    ad_3.ts\n
    vod_4.ts\n
    ad_3.ts\n
    '''
    
    v = VODManifestChecker(manifest, request_url, psn_tag=None, ad_tag='ad', asset_id_tag='vod_')
    print v.ad_pre_number
    print v.ad_post_number
    print v.ad_mid_number
    print v.ad_mid_position_list
