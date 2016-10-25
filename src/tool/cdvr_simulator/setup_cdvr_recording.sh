#!/bin/sh

curl http://127.0.0.1:8082/origin/playlists/setupFixedRecordingID/cdvr_fixed_1~27000
curl http://127.0.0.1:8082/origin/playlists/setupHotRecordingID/cdvr_hot_1~3000
curl http://127.0.0.1:8082/origin/playlists/checkRecordingID