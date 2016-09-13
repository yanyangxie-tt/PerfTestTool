# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import random
import re
import urllib2

def get_random_bit_rate_url(index_url, request_headers, time_out=7, random_bitrate_url=True, random_bitrate_number=None, use_iframe=False, n_bitrate=1, use_sap=False):
    '''
    Get a bit rate URL
    
    @param index_url: 
    @param request_headers: 
    @param time_out:
    @param random_bitrate_url: whether to get random bit rate url or the first bit rate url
    @param random_bitrate_number: how many bitrate url will be used in current performance test
    @param n_bitrate: how many bitrate urls will be return
    
    @return: bitrate url list
    '''
    
    
    req = urllib2.Request(index_url, headers=request_headers)
    bite_url_info = urllib2.urlopen(req, timeout=time_out).read()
    
    bite_url_list = []
    audio_track_url_list = []
    
    for line in bite_url_info.split('\n'):
        if line.strip() == '':
            continue
        elif line.find('EXT-X-I-FRAME-STREAM-INF') >= 0:
            iframe_url = line[line.find('URI="') + len('URI="'):-2]
            if use_iframe:
                bite_url_list.append(iframe_url)
        elif use_sap and line.find('#EXT-X-MEDIA') >= 0:
            for content in line.split(','):
                if content.find('URI=') >= 0:
                    audio_track_url = content[content.find('URI="') + len('URI="'):-1]
                    # bite_url_list.append(audio_track_url)
                    audio_track_url_list.append(audio_track_url)
                    break
        elif line.find('#') == 0:
            continue
        else:
            bite_url_list.append(line.replace('\r', ''))
    
    if len(bite_url_list) == 0:
        return None
    
    if random_bitrate_url:
        if random_bitrate_number is not None:
            if random_bitrate_number >= len(bite_url_list) or random_bitrate_number <= 0:
                random_bitrate_number = len(bite_url_list)
            bite_url_list = bite_url_list[0:random_bitrate_number]
        random.shuffle(bite_url_list)
    random.shuffle(audio_track_url_list)
    
    b_url_list = []
    for i in range(0, n_bitrate):
        b_url_list.append(bite_url_list[i])
        
    if len(audio_track_url_list) > 0 and len(b_url_list) > 1:
        b_url_list = b_url_list[0:-1]
        b_url_list.extend(audio_track_url_list)
        
    return b_url_list

def get_channel_host_from_index_url(index_url):
    flag = '(http://mm\..*.net:*\d*/)'
    p = r'\w*\W*%s[\.\n]*' % (flag)
    t_info = re.findall(p, index_url)
    
    if t_info is not None and len(t_info) > 0:
        return t_info[0]
    
if __name__ == '__main__':
    line = '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="g61136",NAME="English",LANGUAGE="en",URI="index_fake_name_en_audio_1.m3u8",DEFAULT=YES,AUTOSELECT=YES'
    for content in line.split(','):
        print content, content.find('URI=')
        if content.find('URI=') > -1:
            audio_en_url = content[content.find('URI="') + len('URI="'):-1]
            print audio_en_url
            break
