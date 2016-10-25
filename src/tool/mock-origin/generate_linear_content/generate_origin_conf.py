#!/usr/bin/python
# coding:utf-8

'''
@author: yanyang
'''


import os
import re
import string

#data_content_folder = "MP4/stage/2014-02-26/banana_flamb_for_valenti(2660591R22MP464R21MP4350R21MP4500R21MP41000R21MP4150021MP42000R21MP43000R21MP44000R21MP45000)mp4.csmil"

def generate_linear_channel_config(channel_name_list, channel_duration, channel_targetDuration, channel_bit_rate_content_size, channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list):
    lines = []
    for channel_name in channel_name_list:
        lines.append('playlist.%s/index.m3u8=%s%s/%s.m3u8' %(channel_name, data_content_folder, channel_name, channel_name))
        lines.append('config.%s.duration=%s' %(channel_name, channel_duration))
        lines.append('config.%s.targetDuration=%s' %(channel_name, channel_targetDuration))
        lines.append('config.%s.maxReturnContent=%s' %(channel_name, channel_maxReturnContent))
        
        if channel_drm is not None:
            lines.append('config.%s.drm=%s' %(channel_name, channel_drm))
        
        for channel_bit_rate_name in (channel_audio_bit_rate_name_list + channel_video_bit_rate_name_list + channel_iframe_bit_rate_name_list ):
            bit_rate_content_sequence_list = ['0' + str(i) for i in range(1, int(channel_bit_rate_content_size) + 1) if i < 10]
            bit_rate_content_sequence_list += [str(i) for i in range(1, int(channel_bit_rate_content_size) + 1) if i >= 10]
            bit_rate_content_list = ['%s%s/%s_%s_%s.ts' %(data_content_folder, channel_name, channel_name, channel_bit_rate_name,bit_rate_content_sequence) for bit_rate_content_sequence in bit_rate_content_sequence_list]
            lines.append('playlist.%s/%s_%s.m3u8=%s' %(channel_name,channel_name, channel_bit_rate_name,string.join(bit_rate_content_list,',')))
        lines.append('\n')
    return lines

def generate_linear_channel_data_content(channel_name, channel_bit_rate_content_size, channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list, channel_iframe_video_match_dict):
    varient_data_contents = generate_varient_data_content(channel_name, channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list, channel_iframe_video_match_dict)
    bit_rate_data_contents_map = {}
    for channel_bit_rate_name in channel_video_bit_rate_name_list:
        bit_rate_m3u8_contents = generate_bit_rate_date_content(channel_name,channel_bit_rate_name,channel_bit_rate_content_size)
        bit_rate_data_contents_map[channel_bit_rate_name] = bit_rate_m3u8_contents
    
    return varient_data_contents, bit_rate_data_contents_map

def generate_bit_rate_date_content(channel_name,channel_bit_rate_name,channel_bit_rate_content_size):
    lines = []
    lines.append('#EXTM3U')
    lines.append('#EXT-X-VERSION:3')
    lines.append('#EXT-X-MEDIA-SEQUENCE:18')
    lines.append('#EXT-X-TARGETDURATION:%s' %(channel_targetDuration))
    lines.append('#EXT-X-ALLOW-CACHE:NO')
    
    for i in range(1, int(channel_bit_rate_content_size) + 1):
        sequence = '0' + str(i) if i < 10 else str(i)
        lines.append('#EXTINF:6.0,')
        lines.append('%s_%s_%s.ts' %(channel_name,channel_bit_rate_name,sequence))
    return lines

def generate_varient_data_content(channel_name, channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list, channel_iframe_video_match_dict):
    lines = []
    lines.append('#EXTM3U')
    lines.append('#EXT-X-VERSION:3')
    
    if channel_drm is not None:
        lines.append('#EXT-X-FAXS-CM:%s' %(channel_drm))
        
    bandwidth = 2050100
    for channel_bit_rate_name in channel_audio_bit_rate_name_list:
        lines.append('#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="mp4a.40.5"' %(bandwidth))
        lines.append('%s_%s.m3u8' %(channel_name, channel_bit_rate_name))
        bandwidth += 100
    
    for channel_bit_rate_name in channel_video_bit_rate_name_list:
        if channel_iframe_video_match_dict.has_key(channel_bit_rate_name):
            lines.append('#EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="avc1.4d401f",RESOLUTION=256x192,URI="%s_%s.m3u8"' %(bandwidth, channel_name, channel_iframe_video_match_dict[channel_bit_rate_name]))
        lines.append('#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="avc1.4d001f,mp4a.40.5"' %(bandwidth))
        lines.append('%s_%s.m3u8' %(channel_name, channel_bit_rate_name))
        bandwidth += 100
    return lines
      
def load_properties(config_file):
    infos = {}
    if not os.path.exists(config_file):
        return {}
    
    pf = open(config_file, 'rU')
    for line in pf:
        if string.strip(line) == '' or string.strip(line) == '\n' or string.find(line, '#') == 0:
            continue
        line = string.replace(line, '\n', '')
        tmp = line.split("=", 1)
        values = tmp[1].split("#", 1)
        
        infos[string.strip(tmp[0])] = string.strip(values[0])
    pf.close()
    return infos

def write_to_file(lines, out_file_dir, out_file_name, mode='a', is_delete=True):
    if not os.path.exists(out_file_dir):
        os.makedirs(out_file_dir)

    try:
        if not out_file_dir[-1] == os.sep:
            out_file_dir += os.sep
        
        if is_delete and os.path.exists(out_file_dir + out_file_name):
            os.remove(out_file_dir + out_file_name)
        output = open(out_file_dir + out_file_name, mode)
        for line in lines:
            output.write(line + '\n')
    except IOError as err:
        print('Open local file %s error: {0}'.format(err) % (out_file_dir + out_file_name))
    finally:
        output.close()

'''
Get test content name list by test_content_names in configuration file

'''
def get_test_content_name_list(content_names, offset=0):
    p = r'(.*)\[(\d+)~(\d+)\](/*\S*)' #match test_[1,13]
    test_content_list = []

    for c_name in content_names.split(','):
        t = re.findall(p,c_name)
        if len(t) > 0:
            test_content_list += [t[0][0] + str(i + offset) + t[0][3] for i in range(int(t[0][1]), 1 + int(t[0][2]))]
        else:
            test_content_list.append(c_name)
    return test_content_list

def init_config():
    global channel_name_list, channel_duration, channel_targetDuration, channel_bit_rate_content_size, channel_drm
    global channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list, channel_iframe_video_match_dict
    global data_content_folder, channel_maxReturnContent
    
    config_dict = load_properties(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'config.properties')
    channel_names = config_dict['channel_names'] if config_dict.has_key('channel_names') else None
    channel_duration = config_dict['channel_duration'] if config_dict.has_key('channel_duration') else '6'
    channel_targetDuration = config_dict['channel_targetDuration'] if config_dict.has_key('channel_targetDuration') else '6'
    channel_maxReturnContent = config_dict['channel_maxReturnContent'] if config_dict.has_key('channel_maxReturnContent') else '6'
    channel_drm = config_dict['channel_drm'] if config_dict.has_key('channel_drm') else None
    channel_video_bit_rate_names = config_dict['channel_video_bit_rate_names'] if config_dict.has_key('channel_video_bit_rate_names') else None
    channel_audio_bit_rate_names = config_dict['channel_audio_bit_rate_names'] if config_dict.has_key('channel_audio_bit_rate_names') else None
    channel_iframe_bit_rate_names = config_dict['channel_iframe_bit_rate_names'] if config_dict.has_key('channel_iframe_bit_rate_names') else None
    channel_iframe_video_matching = config_dict['channel_iframe_video_matching'] if config_dict.has_key('channel_iframe_video_matching') else None
    channel_bit_rate_content_size = config_dict['channel_bit_rate_content_size'] if config_dict.has_key('channel_bit_rate_content_size') else 1
    data_content_folder = config_dict['channel_data_content_folder'] if config_dict.has_key('channel_bit_rate_content_size') else None
    
    channel_name_list = get_test_content_name_list(channel_names) if channel_names is not None else []
    channel_video_bit_rate_name_list = string.split(channel_video_bit_rate_names, ',') if channel_video_bit_rate_names is not None else []
    channel_audio_bit_rate_name_list = string.split(channel_audio_bit_rate_names, ',') if channel_audio_bit_rate_names is not None else []
    channel_iframe_bit_rate_name_list = string.split(channel_iframe_bit_rate_names, ',') if channel_iframe_bit_rate_names is not None else []
    data_content_folder = data_content_folder + '/' if data_content_folder is not None and data_content_folder[-1]!='/' else data_content_folder

    channel_iframe_video_match_dict = {}
    if channel_iframe_video_matching is not None:
        matchers = string.split(channel_iframe_video_matching, ',')
        for matcher in matchers:
            if matcher.find(':') > 0:
                m_iframe, m_video = string.split(matcher, ':')
                channel_iframe_video_match_dict[m_video]=m_iframe

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    init_config()
    
    channel_config_content_lines = generate_linear_channel_config(channel_name_list, channel_duration, channel_targetDuration, channel_bit_rate_content_size, channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list)
    export_content_dir = here + os.sep + 'linear-contents'
    export_linear_config_file = 'linear-channel-configs.txt'
    print 'Export linear channel configurations into %s' % (export_content_dir + os.sep + export_linear_config_file)
    write_to_file(channel_config_content_lines, export_content_dir, export_linear_config_file)
    
    data_contents_dir = export_content_dir + os.sep + 'data-contents'
    for channel_name in channel_name_list:
        bit_rate_data_contents_dir = data_contents_dir + os.sep + channel_name
        varient_data_contents, bit_rate_data_contents_map = generate_linear_channel_data_content(channel_name, channel_bit_rate_content_size, channel_video_bit_rate_name_list, channel_audio_bit_rate_name_list, channel_iframe_bit_rate_name_list, channel_iframe_video_match_dict)
        
        varient_data_content_file = channel_name + '.m3u8'
        print 'Export linear varient data content into %s' %(bit_rate_data_contents_dir + os.sep + varient_data_content_file)
        write_to_file(varient_data_contents, bit_rate_data_contents_dir, varient_data_content_file)
        
        '''
        for bit_rate_name, bit_rate_contents in bit_rate_data_contents_map.items():
            bit_rate_data_content_file = '%s_%s.m3u8.orig' %(channel_name, bit_rate_name)
            print 'Export linear bit rate data content into %s' %(bit_rate_data_contents_dir + os.sep + bit_rate_data_content_file)
            write_to_file(bit_rate_contents, bit_rate_data_contents_dir, bit_rate_data_content_file)
        '''
    