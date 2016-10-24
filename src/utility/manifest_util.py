# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import random
import re

def get_bitrate_urls(index_response, bitrate_number=2, use_iframe=True, use_sap=True, sap_required=False, random_bitrate=True, bitrate_range=None):
    '''
    Get bitrate URL list
    @param index_response:
    @param use_iframe: parse iframe url
    @param use_sap: parse sap url
    @param sap_required: bitrate list must have sap url
    @param random: random the bitrate url list
    @return: bitrate url list
    '''
    if sap_required is True:
        use_sap = True 
    
    bite_url_list = []
    sap_url_list = []
    for line in index_response.split('\n'):
        line = line.strip()
        if line == '':
            continue
        
        elif use_iframe is True and line.find('EXT-X-I-FRAME-STREAM-INF') >= 0:
            m = re.search('.*URI="(.*)".*', line)
            if m:
                iframe_url = m.groups()[0]
                bite_url_list.append(iframe_url)
            continue
        elif use_sap is True and line.find('#EXT-X-MEDIA') >= 0:
            m = re.search('.*URI="(.*)".*', line)
            if m:
                audio_track_url = m.groups()[0]
                sap_url_list.append(audio_track_url)
                continue
        elif line.find('#') == 0:
            continue
        else:
            bite_url_list.append(line.replace('\r', ''))
    
    if sap_required is True and len(sap_url_list) == 0:
        return []
    else:
        random.shuffle(sap_url_list)
    
    if bitrate_range is not None and 0 < bitrate_range < len(bite_url_list):
        bite_url_list = bite_url_list[0: bitrate_range]
    
    if sap_required is True:
        random.shuffle(bite_url_list)
        bite_url_list.insert(0, sap_url_list[0])
    else:
        bite_url_list.append(sap_url_list[0])
        random.shuffle(bite_url_list)
        
    bite_url_list = bite_url_list[0:bitrate_number] if len(bite_url_list) > bitrate_number else bite_url_list
    if random_bitrate is True: 
        random.shuffle(bite_url_list)
    return bite_url_list

if __name__ == '__main__':
    content = '''
                #EXTM3U
                #EXT-X-VERSION:3
                #EXT-X-FAXS-CM:MIIazgYJKoZIhvcNAQcCoIIavzCCGrsCAQExCzAJBgUrDgMCGgUAMIIKdQYJKoZIhvcNAQcBoIIKZgSCCmIwggpeAgECMIIDjzCCA4sCAQMCAQEELXR2aXYtMWZlMzM4ZTIxODZhMTdlNmUxZTM3ZThkZDlkNTFiYWU4YjE3NTliZDFoMCMMIWNvbS5hZG9iZS5mbGFzaGFjY2Vzcy5yaWdodHMucGxheTBBDCljb20uYWRvYmUuZmxhc2hhY2Nlc3MucmlnaHRzLmxpY2Vuc2VVc2FnZaAUMRIwEAYJKoZIhvcvAwYOoAMBAf+gDQwLNS4yLjEyNzA2MzehCgwIQ09MVU1CVVOjMjEwMC4MKmNvbS5hZG9iZS5mbGFzaGFjY2Vzcy5hdHRyaWJ1dGVzLmFub255bW91czEApYIClDGCApAwFgwMY29udGVudDp0eXBlMQYEBHR2aXYwGAwKY2ttOnBvbGljeTEKBAhDT0xVTUJVUzAkDBNja206Y2xpZW50U2hvcnROYW1lMQ0EC1AwMjAwMDAzMzQzMCgMDmNrbTpkcm1Qcm9maWxlMRYEFGZsYXNoQWNjZXNzLUNPTFVNQlVTMDMMCWRybTprZXlJZDEmBCQ3ZDFiZjRiNS1kYzhiLTg3YzctN2ViNy0zZGIzZDYxOWE0ZTUwQAwQY2ttOmNsaWVudFNlcmlhbDEsBCowMEFFNTc2RTcyRTIyNENBMjMzQ0E0Mzk2OTk3MDA0RjIxNDU5NjFDQTAwQQwKY29udGVudDppZDEzBDFoZ3R2LmNvbUhHVFY0MDcxMzUwMDAyMjU4NTEyLUhHVFY0MDcxMzUwMDAyMjU4NTEzMEUMDm1lZGlhQ29udGVudElkMTMEMWhndHYuY29tSEdUVjQwNzEzNTAwMDIyNTg1MTItSEdUVjQwNzEzNTAwMDIyNTg1MTMwfgwSY2ttOmNsaWVudElzc3VlckRuMWgEZkNOPVAwMjAwMSwgT1U9dXJuOmNvbWNhc3Q6Y2NwOnBraS1jcy10ZCwgTz1Db21jYXN0IENvbnZlcmdlZCBQcm9kdWN0cyBMTEMsIEw9UGhpbGFkZWxwaGlhLCBTVD1QQSwgQz1VUzCBigwTY2ttOmNsaWVudFN1YmplY3REbjFzBHFDTj1QMDIwMDAwMzM0MywgT1U9dXJuOmNvbWNhc3Q6Y2Nw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
                #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="g61136",NAME="English",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="en",URI="http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/vod_test_7975_audio_track_1.m3u8?&IndexName=index.m3u8&BitRelLength=32&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050100&MinBW=2050100&IsIFrame=false&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=true&SAP=English&CODEC=AAC"
                #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2048100,CODECS="mp4a.40.5"
                http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999/vod_test_7975_audio_1.m3u8?&IndexName=index.m3u8&BitRelLength=178&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2048100&MinBW=2050100&IsIFrame=false&IsAudio=true&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC
                #EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050100,CODECS="avc1.4d401f",RESOLUTION=256x192,URI="http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/vod_test_7975_iframe_1.m3u8?&IndexName=index.m3u8&BitRelLength=27&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050100&MinBW=2050100&IsIFrame=true&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC"
                #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050100,CODECS="avc1.4d001f,mp4a.40.5",AUDIO="g61136"
                http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999/vod_test_7975_med_1.m3u8?&IndexName=index.m3u8&BitRelLength=176&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050100&MinBW=2050100&IsIFrame=false&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC
                #EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050200,CODECS="avc1.4d401f",RESOLUTION=256x192,URI="http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/vod_test_7975_iframe_2.m3u8?&IndexName=index.m3u8&BitRelLength=27&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050200&MinBW=2050100&IsIFrame=true&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC"
                #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050200,CODECS="avc1.4d001f,mp4a.40.5",AUDIO="g61136"
                http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999/vod_test_7975_med_2.m3u8?&IndexName=index.m3u8&BitRelLength=176&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050200&MinBW=2050100&IsIFrame=false&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC
                #EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050300,CODECS="avc1.4d401f",RESOLUTION=256x192,URI="http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/vod_test_7975_iframe_3.m3u8?&IndexName=index.m3u8&BitRelLength=27&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050300&MinBW=2050100&IsIFrame=true&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC"
                #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050300,CODECS="avc1.4d001f,mp4a.40.5",AUDIO="g61136"
                http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999/vod_test_7975_med_3.m3u8?&IndexName=index.m3u8&BitRelLength=176&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050300&MinBW=2050100&IsIFrame=false&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC
                #EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050400,CODECS="avc1.4d401f",RESOLUTION=256x192,URI="http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/vod_test_7975_iframe_4.m3u8?&IndexName=index.m3u8&BitRelLength=27&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050400&MinBW=2050100&IsIFrame=true&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC"
                #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2050400,CODECS="avc1.4d001f,mp4a.40.5",AUDIO="g61136"
                http://mm.vod.comcast.net:80/origin/playlists/vod_test_7975/king/9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999/vod_test_7975_med_4.m3u8?&IndexName=index.m3u8&BitRelLength=176&ProviderId=vod_test_7975&AssetId=abcd1234567890123456&StreamType=VOD_T6&DeviceId=X1&PartnerId=hello&dtz=2015-04-09T18:39:05-05:00&sid=VEX_27a749ad-b7af-4f10-ac9f-ebcf2f6ada27&ResourceId=4cb23d3428c74396cddf92159780bf72&BW=2050400&MinBW=2050100&IsIFrame=false&IsAudio=false&HasIFrame=true&HasAudio=true&HasSAP=false&IsSAP=false&CODEC=AAC
'''
    
    for i in  get_bitrate_urls(content, sap_required=True):
        print i 