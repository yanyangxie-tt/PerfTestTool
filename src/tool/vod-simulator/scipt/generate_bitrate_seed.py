'''
@author: yanyang
'''
import string

headers = ['#EXTM3U', '#EXT-X-VERSION:3', '#EXT-X-MEDIA-SEQUENCE:18', '#EXT-X-TARGETDURATION:2', '#EXT-X-ALLOW-CACHE:NO']
bandwidth_template = '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="avc1.4d001f,mp4a.40.5"'

bitrate_seed_content_tag = '#EXTINF:2.0,'
bitrate_seed_content_template = 'bit_rate_fake_name_%s.ts'
bitrate_seed_content_number = 900

line_delimiter='\n'

def generate_bitrate():
    contents = []
    contents += headers
    
    for i in range(0, bitrate_seed_content_number):
        contents.append(bitrate_seed_content_tag)
        contents.append(bitrate_seed_content_template %(i+1))

    return string.join(contents, line_delimiter)
    
    

if __name__ == '__main__':
    print generate_bitrate()
    
    '''
    with open('d:/bitrate-seed.m3u8', 'a+') as p:
        p.write(s)
    '''
    