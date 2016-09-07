import os

from perf.test.model.perf_test import VEXPerfTestBase


if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    print here
    
    config_file = here + os.sep + 'config.properties'
    log_file = here + os.sep + 'vex.log'
    
    v = VEXPerfTestBase(config_file, log_file, log_level='INFO')
    v.demo()