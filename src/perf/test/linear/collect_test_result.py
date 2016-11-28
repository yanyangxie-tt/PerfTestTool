# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

from init_script_env import *
from perf.result.result_analyzer import ResultAnalyzer

class LinearResultAnalyzer(ResultAnalyzer):
    def __init__(self, config_file, collect_traced_data=False, collected_result_before_now=2, **kwargs):
        self.export_concurrent_number = False
        report_dir = here + os.sep + 'reports'
        super(LinearResultAnalyzer, self).__init__(config_file, report_dir, collect_traced_data, collected_result_before_now, **kwargs)

    def reorganize_error_data(self, error_content):
        error_dict = {}
        print '#'*100
        #print error_content.split('\n')
        for line in error_content.split('\n'):
            line = line.strip()
            if line=='':
                continue
            
            contents = line.split('::')
            client_ip, errors = contents[0], contents[1]
            error_list = errors.split('||')
            
            if error_dict.has_key(client_ip):
                error_dict[client_ip] = error_dict[client_ip] + error_list
            else:
                error_dict[client_ip] = error_list
        
        contents = ''
        for client_ip, error_list in error_dict.items():
            contents += '%s:' %(client_ip)
            sorted(error_list)
            for error in error_list:
                contents += '%s\n' %(error)
        return contents

if __name__ == '__main__':
    analyzer = LinearResultAnalyzer(config_file, golden_config_file=golden_config_file)
    analyzer.analysis(True)