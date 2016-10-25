#!/bin/sh

python setup_cdvr_recording.py -H 127.0.0.1 -I cdvr_[1~10]
python setup_cdvr_recording_ad.py -H 127.0.0.1 -I cdvr_[1~10] -S 1,4