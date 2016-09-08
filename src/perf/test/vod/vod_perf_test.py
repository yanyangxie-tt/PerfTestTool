import os

from perf.test.model.perf_test import VEXPerfTestBase

if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    print here
    
    config_file = here + os.sep + 'config.properties'
    log_file = here + os.sep + 'vex.log'
    golden_config_file = here + os.sep + 'config-golden.properties'
    
    
    v = VEXPerfTestBase(config_file, log_file, golden_config_file=golden_config_file)
    v.demo()
