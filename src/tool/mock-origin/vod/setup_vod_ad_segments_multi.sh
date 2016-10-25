#!/bin/sh

#setup vod ad insertion for channel vod_test_1/king ~ vod_test_13/king
python setup_vod_ad_segments.py -H 172.31.10.196 -C vod_test_[1~13]/king -S 1,4