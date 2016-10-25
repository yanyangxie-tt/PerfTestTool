#!/usr/bin/python
# coding:utf-8

'''
@author: yanyang
'''

import os
import re
import string

def generate_vod_asset_config(vod_asset_name_list, vod_asset_duration, vod_asset_targetDuration, vod_asset_bit_rate_name_list, vod_asset_bit_rate_content_size):
    lines = []
    for vod_asset_name in vod_asset_name_list:
        lines.append('playlist.%s/index.m3u8=%s%s/%s.m3u8' %(vod_asset_name, data_content_folder, vod_asset_name, vod_asset_name))
        lines.append('config.%s.duration=%s' %(vod_asset_name, vod_asset_duration))
        lines.append('config.%s.targetDuration=%s' %(vod_asset_name, vod_asset_targetDuration))
        lines.append('config.%s.mediaSequenceStart=%s' %(vod_asset_name, vod_asset_media_sequence))
        
        for vod_asset_bit_rate_name in vod_asset_bit_rate_name_list:
            bit_rate_content_sequence_list = ['0' + str(i) for i in range(1, int(vod_asset_bit_rate_content_size) + 1) if i < 10]
            bit_rate_content_sequence_list += [str(i) for i in range(1, int(vod_asset_bit_rate_content_size) + 1) if i >= 10]
            bit_rate_content_list = ['%s%s/%s_%s_%s.ts' %(data_content_folder, vod_asset_name, vod_asset_name, vod_asset_bit_rate_name,bit_rate_content_sequence) for bit_rate_content_sequence in bit_rate_content_sequence_list]
            lines.append('playlist.%s/%s_%s.m3u8=%s' %(vod_asset_name,vod_asset_name, vod_asset_bit_rate_name,string.join(bit_rate_content_list,',')))
        lines.append('\n')
    return lines

def generate_vod_asset_data_content(vod_asset_name, vod_asset_bit_rate_name_list, vod_asset_bit_rate_content_size):
    varient_data_contents = generate_varient_data_content(vod_asset_name, vod_asset_bit_rate_name_list)
    bit_rate_data_contents_map = {}
    for vod_asset_bit_rate_name in vod_asset_bit_rate_name_list:
        bit_rate_m3u8_contents = generate_bit_rate_date_content(vod_asset_name,vod_asset_bit_rate_name,vod_asset_bit_rate_content_size)
        bit_rate_data_contents_map[vod_asset_bit_rate_name] = bit_rate_m3u8_contents
    
    return varient_data_contents, bit_rate_data_contents_map

def generate_bit_rate_date_content(vod_asset_name,vod_asset_bit_rate_name,vod_asset_bit_rate_content_size):
    lines = []
    lines.append('#EXTM3U')
    lines.append('#EXT-X-VERSION:3')
    lines.append('#EXT-X-MEDIA-SEQUENCE:18')
    lines.append('#EXT-X-TARGETDURATION:%s' %(vod_asset_targetDuration))
    lines.append('#EXT-X-ALLOW-CACHE:NO')
    
    for i in range(1, int(vod_asset_bit_rate_content_size) + 1):
        sequence = '0' + str(i) if i < 10 else str(i)
        lines.append('#EXTINF:6.0,')
        lines.append('%s_%s_%s.ts' %(vod_asset_name,vod_asset_bit_rate_name,sequence))
    return lines

def generate_varient_data_content(vod_asset_name, vod_asset_bit_rate_name_list):
    lines = []
    lines.append('#EXTM3U')
    lines.append('#EXT-X-VERSION:3')
    
    bandwidth_start = 2050100
    for index, vod_asset_bit_rate_name in enumerate(vod_asset_bit_rate_name_list):
        lines.append('#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="avc1.4d001f,mp4a.40.5"' %(bandwidth_start + index * 100))
        lines.append('%s_%s.m3u8' %(vod_asset_name, vod_asset_bit_rate_name))
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
    global vod_asset_name_list, vod_asset_duration, vod_asset_targetDuration, vod_asset_bit_rate_name_list, vod_asset_bit_rate_content_size
    global data_content_folder, vod_asset_media_sequence
    
    config_dict = load_properties(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'config.properties')
    vod_asset_names = config_dict['vod_asset_names'] if config_dict.has_key('vod_asset_names') else None
    vod_asset_duration = config_dict['vod_asset_duration'] if config_dict.has_key('vod_asset_duration') else '6'
    vod_asset_targetDuration = config_dict['vod_asset_targetDuration'] if config_dict.has_key('vod_asset_targetDuration') else '6'
    vod_asset_media_sequence = config_dict['vod_asset_media_sequence'] if config_dict.has_key('vod_asset_media_sequence') else '6'
    vod_asset_bit_rate_names = config_dict['vod_asset_bit_rate_names'] if config_dict.has_key('vod_asset_bit_rate_names') else None
    vod_asset_bit_rate_content_size = config_dict['vod_asset_bit_rate_content_size'] if config_dict.has_key('vod_asset_bit_rate_content_size') else 1
    data_content_folder = config_dict['vod_asset_data_content_folder'] if config_dict.has_key('vod_asset_bit_rate_content_size') else None
    
    vod_asset_name_list = get_test_content_name_list(vod_asset_names) if vod_asset_names is not None else []
    vod_asset_bit_rate_name_list = string.split(vod_asset_bit_rate_names, ',') if vod_asset_bit_rate_names is not None else []
    data_content_folder = data_content_folder + '/' if data_content_folder is not None and data_content_folder[-1]!='/' else data_content_folder

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    init_config()
    
    vod_asset_config_content_lines = generate_vod_asset_config(vod_asset_name_list, vod_asset_duration, vod_asset_targetDuration, vod_asset_bit_rate_name_list, vod_asset_bit_rate_content_size)
    export_content_dir = here + os.sep + 'vod-contents'
    export_vod_config_file = 'vod_asset-configs.txt'
    print 'Export vod_asset configurations into %s' % (export_content_dir + os.sep + export_vod_config_file)
    write_to_file(vod_asset_config_content_lines, export_content_dir, export_vod_config_file)
    
    data_contents_dir = export_content_dir + os.sep + 'data-contents'
    for vod_asset_name in vod_asset_name_list:
        bit_rate_data_contents_dir = data_contents_dir + os.sep + vod_asset_name
        varient_data_contents, bit_rate_data_contents_map = generate_vod_asset_data_content(vod_asset_name, vod_asset_bit_rate_name_list, vod_asset_bit_rate_content_size)
        
        varient_data_content_file = vod_asset_name + '.m3u8'
        print 'Export vod varient data content into %s' %(bit_rate_data_contents_dir + os.sep + varient_data_content_file)
        write_to_file(varient_data_contents, bit_rate_data_contents_dir, varient_data_content_file)
        
        for bit_rate_name, bit_rate_contents in bit_rate_data_contents_map.items():
            bit_rate_data_content_file = '%s_%s.m3u8.orig' %(vod_asset_name, bit_rate_name)
            print 'Export vod bit rate data content into %s' %(bit_rate_data_contents_dir + os.sep + bit_rate_data_content_file)
            write_to_file(bit_rate_contents, bit_rate_data_contents_dir, bit_rate_data_content_file)
        
    