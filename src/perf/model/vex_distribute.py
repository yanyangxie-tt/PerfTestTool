from perf.model.configuration import Configurations
from utility import fab_util


class DistributeEnv(Configurations):
    def __init__(self, config_file, **kwargs):
        '''@param config_file: configuration file, must be a properties file'''
        super(DistributeEnv, self).__init__(config_file, **kwargs)
        self.set_fabric_env()
    
    def set_fabric_env(self):
        self._set_attr('test_machine_port', '22')
        self._set_attr('test_machine_username', 'root')
        
        if not hasattr(self, 'test_machine_pubkey') and not hasattr(self, 'test_virtual_machine_password'):
            print 'pubkey and password must have one'
            exit(1)
        
        if not hasattr(self, 'test_machine_hosts'):
            print 'Test machine hosts is required'
            exit(1)
        elif type(self.test_machine_hosts) is str:
            self.test_machine_hosts = [self.test_machine_hosts, ]
        
        if hasattr(self, 'test_machine_username'): fab_util.set_user(self.test_machine_username)
        if hasattr(self, 'test_machine_port'): fab_util.set_port(self.test_machine_port)
        if hasattr(self, 'test_machine_pubkey'): fab_util.set_key_file(self.test_machine_pubkey)
        if hasattr(self, 'test_virtual_machine_password'): fab_util.set_password(self.test_virtual_machine_password)
