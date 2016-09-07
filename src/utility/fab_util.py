# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from fabric.api import *
from fabric.colors import *
from fabric.exceptions import CommandTimeout
from fabric.operations import run, local, put, get
from fabric.state import env


# host and role lists will be merge to one list of deduped hosts while execute task
def setRoles(role_name, host_list, user=None, port=None, roledefs_dict=None):
    '''host_list=['root@172.31.13.47:22', 'root@172.31.13.48', ]'''
    
    if host_list is None or type(host_list) != list:
        return
    
    # env.roledefs = { 'testserver': ['user1@host1:port1',], 'realserver': ['user2@host2:port2', ] }
    if user:
        host_list = ['%s@%s' % (user, host) for host in host_list if host.find(user) < 0 ]
    
    if port:
        host_list = ['%s:%s' % (host, port)  for host in host_list if host.find(':') < 0 ]
    
    env.roledefs.update({role_name:host_list})
    if roledefs_dict and type(roledefs_dict) is dict:
        env.roledefs.update(roledefs_dict)

def set_hosts(hosts):
    # env.hosts = ['user@host1:port', 'host2']
    env.hosts += hosts if type(hosts) is list else [hosts, ]

def setKeyFile(key_filename):
    if key_filename is None or key_filename == '':
        return
    env.key_filename = key_filename

def set_user(user):
    if user is None or user == '':
        return
    env.user = user
    
def set_password(password):
    if password is None or password == '':
        return
    env.password = password

def set_host_password_matching(host_past_word_dict):
    if type(host_past_word_dict) is not dict:
        return
    
    '''
        env.passwords = {
            'host1': "pwdofhost1",
            'host2': "pwdofhost2",
            'host3': "pwdofhost3",
        }
    '''
    env.passwords.update(host_past_word_dict)

# update env setttings
def update_env_settings(env_settings_dict={}):
    if type(env_settings_dict) is not dict:
        return
    '''
        env = _AttributeDict({
            'all_hosts': [],
            'colorize_errors': False,
            'command': None,
            'command_prefixes': [],
            'cwd': '',  # Must be empty string, not None, for concatenation purposes
            'dedupe_hosts': True,
            'default_port': default_port,
            'eagerly_disconnect': False,
            'echo_stdin': True,
            'exclude_hosts': [],
            'gateway': None,
            'host': None,
            'host_string': None,
            'lcwd': '',  # Must be empty string, not None, for concatenation purposes
            'local_user': _get_system_username(),
            'output_prefix': True,
            'passwords': {},
            'path': '',
            'path_behavior': 'append',
            'port': default_port,
            'real_fabfile': None,
            'remote_interrupt': None,
            'roles': [],
            'roledefs': {},
            'shell_env': {},
            'skip_bad_hosts': False,
            'ssh_config_path': default_ssh_config_path,
            'ok_ret_codes': [0],     # a list of return codes that indicate success
            # -S so sudo accepts passwd via stdin, -p with our known-value prompt for
            # later detection (thus %s -- gets filled with env.sudo_prompt at runtime)
            'sudo_prefix': "sudo -S -p '%(sudo_prompt)s' ",
            'sudo_prompt': 'sudo password:',
            'sudo_user': None,
            'tasks': [],
            'use_exceptions_for': {'network': False},
            'use_shell': True,
            'use_ssh_config': False,
            'user': None,
            'version': get_version('short')
        })
    '''
    env.update(env_settings_dict)

'''
下述的方法，需要在@task的函数中运行。否则env的环境设置不起作用
@task
def _test_host_type():
    fab_run_command('uname -s')

execute(_test_host_type)
'''
def fab_run_command(command, is_local=False, command_path=None, command_prefix=None, pty=False, warn_only=True, timeout=3, ex_abort=False):
    '''
    @param is_local: local or remote 
    @param command_path: command path
    @param command_prefix: the command will be 'command_prefix && command'
    @param warn_only: if warn_only=False, then throw a exception while error. If =True, just ignore the exception.
    @param ex_abort: if warn_only=True and meeting exception, then exit main process
    '''
    result = None
    
    if is_local:
        if command_path is not None:
            with lcd(command_path):
                if command_prefix is not None:
                    with prefix(command_prefix):
                        result = local(command)
                else:
                    result = local(command) 
        else:
            if command_prefix is not None:
                with prefix(command_prefix):
                    result = local(command)
            else:
                result = local(command)
    else:
        try:
            if command_path is not None:
                with cd(command_path):
                    if command_prefix is not None:
                        with prefix(command_prefix):
                            result = run(command, pty=pty, warn_only=warn_only, timeout=timeout)
                    else:
                        result = run(command, pty=pty, warn_only=warn_only, timeout=timeout) 
            else:
                if command_prefix is not None:
                    with prefix(command_prefix):
                        result = run(command, pty=pty, warn_only=warn_only, timeout=timeout)
                else:
                    result = run(command, pty=pty, warn_only=warn_only, timeout=timeout)
        except CommandTimeout, e:
            print e
    
    if result and result.failed:
        print red(u'Failed to execute command 【%s】' % (command))
        if ex_abort:
            abort("abort!!!")
    return result

def fab_shutdown_service(service_tag='tomcat', service_shutdown_command=None, is_local=False, sleep=5):
    if service_shutdown_command:
        try:
            local(service_shutdown_command) if is_local else run(service_shutdown_command, pty=False, warn_only=True)
            
            import time
            time.sleep(sleep)
        except:
            pass
            # print 'Stop service %s failed by command [%s]' % (service_tag, service_shutdown_command)
    
    if is_local:
        pid = local("ps gaux | grep %s | grep -v grep | awk '{print $2}'" % (service_tag))
    else:
        pid = run("ps gaux | grep %s | grep -v grep | awk '{print $2}'" % (service_tag), pty=False, warn_only=True)
        
    if pid == '':
        return

    pids = str(pid).splitlines()
    if pids is None or len(pids) == 0:
        print 'Service \'%s\' is not running till now.' % (service_tag)
    else:
        print 'Service \'%s\' is running, execute kill.' % (service_tag)
        for p_id in pids:
            local('kill -9 %s' % (p_id)) if is_local else run('kill -9 %s' % (p_id), pty=False, warn_only=True) 

def upload_file_or_dir_to_remote(local_path, remote_path):
    '''
        Upload one or more files to a remote host. 
        @param local_path: may be a relative or absolute local file or directory path
        @param remote_path: absolute local directory path
    '''
    if not os.path.exist(local_path):
        exit()
    
    # make the directory in remote machine
    with cd('/tmp'):
        run('mkdir -p %s' % (remote_path))
        put(local_path, remote_path)

def download_file_or_dir_to_local(local_path, remote_path):
    '''
        Download one or more files from a remote host. 
        @param local_path: may be a relative or absolute directory path
        @param remote_path: absolute remote directory path
    '''
    
    if not os.path.exist(local_path):
        os.makedirs(local_path)

    get(remote_path, local_path)

def _test_host_type():
    result = fab_run_command('ls /home/yanyang', is_local=False, warn_only=False)
    print '******'
    print result.failed
    # print result
    
    result = fab_run_command('12345', warn_only=True, ex_abort=True)
    print 1234

if __name__ == '__main__':
    host = 'root@54.169.51.190'
    key_file = '/Users/xieyanyang/work/ttbj/ttbj-keypair.pem'
    
    set_hosts(host)
    setKeyFile(key_file)
    execute(_test_host_type)
    
    
