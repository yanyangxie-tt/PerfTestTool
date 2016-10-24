'''
@author: yanyang
'''
import string

headers = ['#EXTM3U', '#EXT-X-VERSION:3', ]

iframe_seed = True
video_iframe_template = '#EXT-X-I-FRAME-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="avc1.4d401f",RESOLUTION=256x192,URI="index_fake_name_iframe_%s.m3u8"'
video_bandwidth_template = '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="avc1.4d001f,mp4a.40.5"'
video_content_template = 'index_fake_name_med_%s.m3u8'
video_content_number=11

audio_seed = True
audio_bandwidth_template = '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%s,CODECS="mp4a.40.5"'
audio_content_template = 'index_fake_name_audio_%s.m3u8'
audio_content_number = 1

line_delimiter='\n'


def generate_index():
    contents = []
    contents += headers
    
    if audio_seed:
        for i in range(0, audio_content_number):
            contents.append(audio_bandwidth_template %(2048100 + i * 100))
            contents.append(audio_content_template %(i+1))
    
    for i in range(0, video_content_number):
        if iframe_seed:
            contents.append(video_iframe_template %(2050100 + i * 100, i+1))
        contents.append(video_bandwidth_template %(2050100 + i * 100))
        contents.append(video_content_template %(i+1))
    
    return string.join(contents, line_delimiter)

if __name__ == '__main__':
    print generate_index()
    
    '''
    with open('d:/bitrate-seed.m3u8', 'a+') as p:
        p.write(s)
    '''
    