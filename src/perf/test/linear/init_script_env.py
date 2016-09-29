import os
import sys
sys.path.append(os.path.join(os.path.split(os.path.realpath(__file__))[0], "../../.."))

here = os.path.dirname(os.path.realpath(__file__))
config_file = here + os.sep + 'config.properties'
golden_config_file = here + os.sep + 'config-golden.properties'

perf_test_remote_script_dir = '/tmp/perf-test-script'
perf_test_remote_result_default_dir = '/tmp/load-test-result'

perf_test_machine_group = 'perf_test_machines'
perf_test_script_zip_name = 'perf-test.zip'
perf_test_script_zip_file_dir = '/tmp'
perf_test_script_zip_file_name = perf_test_script_zip_file_dir + os.sep + perf_test_script_zip_name

load_test_multiple_script_file_name = 'execute_multi_test.py'
load_test_sigle_process_script_file = 'linear_perf_test.py'
load_test_script_file_name = os.path.dirname(os.path.abspath(__file__)) + os.sep + load_test_sigle_process_script_file

final_test_report_file_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'reports'
final_test_monitor_file_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'system_monitors'
