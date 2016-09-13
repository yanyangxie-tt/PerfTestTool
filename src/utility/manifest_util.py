# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import random

def get_bitrate_urls(index_response, birate_number=1, use_iframe=True, use_sap=True):
    '''
    Get bitrate URL list
    @param index_response:
    @param use_iframe: parse iframe url
    @param use_sap: parse audio url
    
    @return: bitrate url list
    '''
    
    bite_url_list = []
    for line in index_response.split('\n'):
        if line.strip() == '':
            continue
        
        elif use_iframe and line.find('EXT-X-I-FRAME-STREAM-INF') >= 0:
            iframe_url = line[line.find('URI="') + len('URI="'):-2]
            if use_iframe:
                bite_url_list.append(iframe_url)
                
        elif use_sap and line.find('#EXT-X-MEDIA') >= 0:
            for content in line.split(','):
                if content.find('URI=') >= 0:
                    audio_track_url = content[content.find('URI="') + len('URI="'):-1]
                    bite_url_list.append(audio_track_url)
                    break
        elif line.find('#') == 0:
            continue
        else:
            bite_url_list.append(line.replace('\r', ''))
    random.shuffle(bite_url_list)
    return bite_url_list[0:birate_number] if len(bite_url_list) > birate_number else bite_url_list

