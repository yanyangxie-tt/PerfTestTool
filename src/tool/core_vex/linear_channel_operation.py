#!/usr/bin/python
# -*- coding=utf-8 -*-

'''
@author: yanyang
'''
import os
import requests

#"adsZoneBased"/"adsFullAddr"/"ComcastZoneBased"/"ComcastFullAddr" 

host = '54.169.6.129'
port = '8080'

vex_linear_api_base = 'http://%s:%s/vex/api/linearChannels' %(host, port)
#headers = {'Authorization':auth_token,'content-type':'application/x-www-form-urlencoded'}
auth_token = 'Basic YWRtaW5AdGhpc3RlY2guY29tOmFkbWlu'
headers = {'Authorization':auth_token}

channel_number = 250
channel_name_prefix = 'tve_test' # t6_test, tve_test
channel_steam_type = 'TVELinear' # Optional is TVELinear or T6Linear
channel_view_expansion_frequency = 12000 # TVE is 12000, T6 is 6000
channel_grouping_strategy = 'ComcastFullAddr' #"adsZoneBased"/"adsFullAddr"/"ComcastZoneBased"/"ComcastFullAddr"
channel_origin_id = '538ed480e4b0fe62bd198edb'

#get exist linear channel ids
def get_linear_channels(channel_name_prefix):
    url = vex_linear_api_base + "/listChannel?partAlias=%s" %(channel_name_prefix)
    r = requests.get(url, headers=headers)
    response_json = r.json()
    
    channel_ids = []
    if len(response_json) > 0:
        for channel_json in response_json['channels']:
            cid = channel_json['id']
            channel_ids.append(cid)
    
    return channel_ids

def delete_linear_channel_by_ids(cids=[]):
    for cid in cids:
        url = vex_linear_api_base + '/' + cid
        requests.delete(url, headers=headers)

def add_linear_channel(channel_number, channel_name_prefix, channel_steam_type, channel_grouping_strategy, channel_origin_id):
    headers['Content-Type']='application/xml'
    
    with open(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'linear_template.xml') as p:
        content_template = p.read()
        content_template = content_template.replace('\n','')
    
    if content_template is not None:
        for i in range(1, channel_number + 1):
            channel_name = channel_name_prefix + '_' + str(i)
            data = content_template %(channel_grouping_strategy,channel_name,channel_name,channel_name_prefix,i,channel_origin_id,channel_steam_type, str(channel_view_expansion_frequency))
            r = requests.post(vex_linear_api_base, data, headers=headers)
            print r.text
    
if __name__ == '__main__':
    channel_ids = get_linear_channels(channel_name_prefix)
    delete_linear_channel_by_ids(channel_ids)
    #add_linear_channel(channel_number, channel_name_prefix, channel_steam_type, channel_grouping_strategy, channel_origin_id)