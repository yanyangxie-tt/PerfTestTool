#!/bin/sh

#setup ad insertion for channel test_1 ~ test_13
python setup_linear_ad_segments.py -H 172.31.5.141 -C test_[1~13] -S 100/10
