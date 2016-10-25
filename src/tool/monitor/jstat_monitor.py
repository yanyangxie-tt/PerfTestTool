import os
import time
import string

def get_pids(keyword):
    command = "ps gaux | grep %s | grep -v grep | awk '{print $2}'" %(keyword)
    pids = os.popen(command).readlines()
    return [int(pid.replace('\n','')) for pid in pids]

def run_command(command):
    return os.popen(command).readlines()

def get_gc_status(java_pid, java_path='/usr/local/java/jdk1.7.0_60'):
    os.chdir(java_path + os.sep + 'bin')
    jstat_command = './jstat -gc %s 1 1' %(java_pid)
    return run_command(jstat_command)[1].replace('\n','')

def get_jmap_histo_info(java_pid, java_path='/usr/local/java/jdk1.7.0_60'):
    jstat_command = 'su tomcat -c "jmap -histo:live %s | head -30"' %(java_pid)
    jstat_info_list = run_command(jstat_command)
    return jstat_info_list[2:-1]

def write_to_file(lines, out_file_dir, out_file_name, mode='a', is_delete=True):
    if not os.path.exists(out_file_dir):
        os.makedirs(out_file_dir)

    try:
        if not out_file_dir[-1] == os.sep:
            out_file_dir += os.sep
        
        if is_delete and os.path.exists(out_file_dir + out_file_name):
            #print 'remove older file %s' %(out_file_dir + out_file_name)
            os.remove(out_file_dir + out_file_name)
        output = open(out_file_dir + out_file_name, mode)
        output.writelines(lines)
    except IOError as err:
        print('Open local file %s error: {0}'.format(err) % (out_file_dir + out_file_name))
    finally:
        output.close()

if __name__ == '__main__':
    export_dir = '/tmp/'
    export_jstat_file = 'jstat_gc.info'
    export_jmap_file = 'jmap.info'
    tomcat_pid = get_pids('tomcat')[0]
    
    i = 0
    while 1:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        os.popen("echo %s %s >> %s" %(current_time, get_gc_status(tomcat_pid),export_dir + export_jstat_file))
        
        if i%30 == 0:
            write_to_file([current_time] + get_jmap_histo_info(tomcat_pid),export_dir, export_jmap_file, is_delete=False)
        time.sleep(1)
        i += 1