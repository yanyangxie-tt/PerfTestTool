#!/usr/bin/python
# coding:utf-8

'''
Created on 2014-3-13
@summary: This script is to batch setup origin proxy and then start it.

@author: yanyang.xie
'''
import os
import sys
import time
import traceback
import subprocess

# src_origin_proxy is a unzipped origin proxy file which is as seed of creating multi orgin proxy.
src_origin_proxy_par_dir = '/root/'
src_origin_proxy_dir_name = 'origin-proxy-1.1.0-SNAPSHOT'
src_origin_proxy_port = 8090 # port in seed origin proxy conf file
src_origin_proxy_edge_origin = 'origin-server-ip:port' # edge mock origin in seed origin proxy conf file

# dest_origin_proxy is the new origin proxy
dest_origin_proxy_par_dir = '/root/origin-proxys'
dest_origin_proxy_dir_name = 'origin-proxy' # dest origin proxy folder name
dest_origin_proxy_edge_origin = '172.31.5.141:8082' # real mock origin server host

origin_proxy_port_start_number = 8100
origin_proxy_number = 50

def setup_new_origin_proxy(src_origin_proxy_par_dir, src_origin_proxy_dir_name, dest_origin_proxy_par_dir, dest_origin_proxy_dir_name, proxy_port_start_number, proxy_sequence_number):
    if not src_origin_proxy_par_dir[-1] == os.sep:
        src_origin_proxy_par_dir += os.sep
    
    if not dest_origin_proxy_par_dir[-1] == os.sep:
        dest_origin_proxy_par_dir += os.sep
        
    src_origin_proxy_dir_path = src_origin_proxy_par_dir + src_origin_proxy_dir_name
    dest_origin_proxy_dir_path = dest_origin_proxy_par_dir + dest_origin_proxy_dir_name + '-' + str(proxy_port_start_number + proxy_sequence_number)
    
    if not os.path.exists(src_origin_proxy_dir_path):
        print 'Default origin proxy simulator is not exist, please check it first.'
        return None

    try:
        if not os.path.exists(dest_origin_proxy_par_dir):
            os.makedirs(dest_origin_proxy_par_dir)
        
        if os.path.exists(dest_origin_proxy_dir_path):
            os.system('rm -rf %s' %(dest_origin_proxy_dir_path))
        
        # copy one origin proxy simulator    
        print 'cp -rf %s %s' % (src_origin_proxy_dir_path, dest_origin_proxy_dir_path)
        os.system('cp -rf %s %s' % (src_origin_proxy_dir_path, dest_origin_proxy_dir_path))
        
        # set new port
        print "sed '/origin.proxy.port=/s/%s/%s/g' %s>%s" % (src_origin_proxy_port, proxy_port_start_number + proxy_sequence_number, dest_origin_proxy_dir_path + '/conf/origin-proxy.properties',dest_origin_proxy_dir_path + '/conf/origin-proxy.properties.merge')
        os.system("sed '/origin.proxy.port=/s/%s/%s/g' %s>%s" % (src_origin_proxy_port, proxy_port_start_number + proxy_sequence_number, dest_origin_proxy_dir_path + '/conf/origin-proxy.properties', dest_origin_proxy_dir_path + '/conf/origin-proxy.properties.merge'))
        os.system('mv %s %s' %(dest_origin_proxy_dir_path + '/conf/origin-proxy.properties.merge', dest_origin_proxy_dir_path + '/conf/origin-proxy.properties'))
        
        # set new mock origin
        print "sed '/mock.origin.server=/s/%s/%s/g' %s>%s" % (src_origin_proxy_edge_origin, dest_origin_proxy_edge_origin, dest_origin_proxy_dir_path + '/conf/origin-proxy.properties',dest_origin_proxy_dir_path + '/conf/origin-proxy.properties.merge')
        os.system("sed '/mock.origin.server=/s/%s/%s/g' %s>%s" % (src_origin_proxy_edge_origin, dest_origin_proxy_edge_origin, dest_origin_proxy_dir_path + '/conf/origin-proxy.properties', dest_origin_proxy_dir_path + '/conf/origin-proxy.properties.merge'))
        os.system('mv %s %s' %(dest_origin_proxy_dir_path + '/conf/origin-proxy.properties.merge', dest_origin_proxy_dir_path + '/conf/origin-proxy.properties'))
        
        # make run.sh and shutdown.sh executable
        os.system('chmod a+x %s/*.sh' % (dest_origin_proxy_dir_path))
        os.system('dos2unix %s/*.sh' % (dest_origin_proxy_dir_path))
        
        return dest_origin_proxy_dir_path
    except:
        traceback.print_exc()
        return None

def setup_multi_origin_proxy(src_origin_proxy_par_dir, src_origin_proxy_dir_name, dest_origin_proxy_par_dir, dest_origin_proxy_dir_name, proxy_port_start_number, proxy_sequence_number):
    new_origin_proxy_list = []
    
    for i in range(0, proxy_sequence_number):
        dest_origin_proxy_dir_path = setup_new_origin_proxy(src_origin_proxy_par_dir, src_origin_proxy_dir_name, dest_origin_proxy_par_dir, dest_origin_proxy_dir_name, proxy_port_start_number, i)
        if not dest_origin_proxy_dir_path:
            break
        
        new_origin_proxy_list.append(dest_origin_proxy_dir_path)
    return new_origin_proxy_list

def start_all_origin_proxy(origin_proxy_simulator_list):
    print origin_proxy_simulator_list
    for origin_proxy_simulator in origin_proxy_simulator_list:
        print 'start up %s' %(origin_proxy_simulator)
        os.chdir(origin_proxy_simulator)
        subprocess.Popen('nohup ./run.sh &', shell=True, stdout=subprocess.PIPE)
        time.sleep(1)

def shutdown_all_origin_proxy(origin_proxy_simulator_list):
    print origin_proxy_simulator_list
    for origin_proxy_simulator in origin_proxy_simulator_list:
        print 'shutdown origin simulators'
        os.chdir(origin_proxy_simulator)
        subprocess.Popen('./shutdown.sh', shell=True)
        time.sleep(1)
        break
        
if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'stop'
    
    print '#' * 50
    if command == 'setup':
        print 'Start to setup origin proxys'
        origin_proxy_list = setup_multi_origin_proxy(src_origin_proxy_par_dir, src_origin_proxy_dir_name, dest_origin_proxy_par_dir, dest_origin_proxy_dir_name, origin_proxy_port_start_number, origin_proxy_number)
        print origin_proxy_list
        print 'Finish to setup origin proxys'
    elif command == 'start':
        print 'Start up origin proxys'
        origin_proxy_list = [dest_origin_proxy_par_dir + os.sep + dest_origin_proxy_dir_name + '-' + str(origin_proxy_port_start_number + sequence_number) for sequence_number in range(origin_proxy_number)]
        start_all_origin_proxy(origin_proxy_list) #['/root/origin-proxys/origin-proxy-8100', '/root/origin-proxys/origin-proxy-8101']
        print 'Finish to start up origin proxys, Use netstat -an | grep 81 to get status'
        p = subprocess.Popen('netstat -an | grep 81', shell=True, stdout=subprocess.PIPE)
        print p.stdout.read()
    else:
        print 'Shutdown origin proxys'
        origin_proxy_list = [dest_origin_proxy_par_dir + os.sep + dest_origin_proxy_dir_name + '-' + str(origin_proxy_port_start_number + sequence_number) for sequence_number in range(origin_proxy_number)]
        shutdown_all_origin_proxy(origin_proxy_list)
        print 'Finish to shutdown origin proxys, Use netstat -an | grep 81 to get status'
        p = subprocess.Popen('netstat -an | grep 81', shell=True, stdout=subprocess.PIPE)
        print p.stdout.read()
        
