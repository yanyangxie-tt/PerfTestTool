'''
Created on 2014-6-26

@author: yanyang
'''

# Many error log has same meaning, but just special info is different, so should ignore those info
vex_merge_rule_list = [ r'callback(/.*),',
                    r'Failed to load data from memcached(.*)',
                    r'General error. Execute HttpManifestFileConsumer used(.*)',
                    r'VexLinearExecutor-DistributedExecutor failed to execute sub task:TransactionID(.*)',
                    r'VexCDVRExecutor-VEXExecutor failed to get next transactionId(.*)',
                    r'VexLinearExecutor-VEXExecutor failed to get next transactionId(.*)',
                    r'Failed to get http response from: http://(.*)/callback, due to: Read timed out',
                    r'General error. This bit rate playlist does not know its\' bandwidth due to variant playlist cache miss! bandwidth: 0(.*)',
                    r'Failed to save data to memcached. Failed to put expanded manifest to memcached( with key.*)',
                    r'Failed to load data from memcached.(.*)There is no available connection at this moment',
                    r'Failed to save data to memcached. directorCacheKey(.*)',
                    r'Failed to save data to memcached. key:(.*)',
                    r'Get ADS decision failed. director request content(.*)',
                    r'Failed to get http response from:(.*)/origin/playlists(.*)',
                    r'Trying to connect to(.*)11211(.*)',
                    r'VexLinearExecutor-DistributedExecutor get current task status after timeout(.*)',
                    r'Failed to get http response from: http://ccr.cdvr.comcast.net(.*)',
                    r'Get remote manifest failed. Failed to get the variant manifest file(.*)',
                    r'Get remote manifest failed. Date(.*)',
                    r'(.*)capture dateTime info is empty(.*)',
                    r'VexCDVRExecutor-DistributedExecutor get current task status after timeout(.*)',
                    r'(.*)Failed to get http response from: http://(.*)/spotlink-router/adsrs/PlacementRequest(.*)',
                    r'Get remote manifest failed. requested ad variant uri(.*)',
                    r'Does not insert an ad because the bit rate is incompatible. Client sent invalid abr bandwidth: 0, VEX have to choose the lowest bit rate AD content(.*)',
                    ]

vex_fe_merge_rule_list = [r'Not found playlist cache, got default playlist(.*)',
                    r'General error Error sending cache miss request(.*)',
                    r'no clientview for key channelStore(.*)',
                    r'Not found playlist cache, got default playlist: {null} for key(.*)',
                    ]

vex_director_merge_rule_list = [r'Send placement status notification to ADS failed. There is no AdView cached for client(.*)',
                                ]
