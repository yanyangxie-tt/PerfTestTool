# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import random
import socket
import string

def get_local_IP():
    return socket.gethostbyname(socket.gethostname())

def ip2number(n):
    return sum([256 ** j * int(i) for j, i in enumerate(n.split('.')[::-1])])

def number2ip(ip):
    return '.'.join([str(ip / (256 ** i) % 256) for i in range(3, -1, -1)])

def generate_random_ip(ip_segment_index=3, ip_segment_range=[0, 255]):
    # if ip_segment_index is set, will replace its value by a random value in ip_segment_range
    rip = number2ip(10000 * random.randint(1, 100000) + random.randint(0, 1000000000))
    r_ip_segments = rip.split('.')
    
    new_r_ip_segments = []
    for i in range(0, len(r_ip_segments)):
        if ip_segment_index == i:
            new_r_ip_segments.append(str(random.randint(ip_segment_range[0], ip_segment_range[-1])))
        else:
            new_r_ip_segments.append(r_ip_segments[i])
    
    return string.join(new_r_ip_segments, '.') 

if __name__ == '__main__':
    print generate_random_ip(ip_segment_range=[0, 9])
