# -*- coding=utf-8 -*-
# author: yanyang.xie@thistech.com

from logging import StreamHandler
import logging
from logging.handlers import RotatingFileHandler
import os

# formatter is a bundle of standard string
log_format = logging.Formatter('%(asctime)s [%(filename)s] [line:%(lineno)4d] [%(levelname)s] %(message)s')
rotate_file_size = 1000 * 1024 * 1024
log_level_list = logging._levelNames.keys()

def setup_logger(log_file, name=None, log_level='INFO', formatter=log_format, rotated_file_size=rotate_file_size, rotated_backup_file_number=5):
    log_dir = os.path.split(log_file)[0]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if log_level not in log_level_list:
        log_level = log_level_list[0]

    rt_handler = RotatingFileHandler(log_file, maxBytes=rotate_file_size, backupCount=rotated_backup_file_number)
    rt_handler.setFormatter(formatter)
    
    sm_handler = StreamHandler()
    sm_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.addHandler(rt_handler)
    logger.addHandler(sm_handler)
    logger.setLevel(log_level)

def setup_logger_from_config_file(log_config_file, name=None, log_level='DEBUG'):
    '''Configured python logging module from a configuration file'''
    logging.config.fileConfig(log_config_file)
   
    # name must be match one of configured logger key names, such as 'root' or 'simpleExample' in following logger.conf
    logger = logging.getLogger(name)
    if log_level is not None:
        logger.setLevel(log_level)

    '''
        #logger.conf
        # root is for all, simpleExample is to your app
        [loggers]
        keys=root,simpleExample
        
        [handlers]
        keys=consoleHandler
        
        [formatters]
        keys=simpleFormatter
        
        [logger_root]
        level=DEBUG
        handlers=rotateFileHandler
        
        [logger_simpleExample]
        level=DEBUG
        handlers=consoleHandler
        qualname=simpleExample
        propagate=0
        
        [handler_rotateFileHandler]
        class=handlers.RotatingFileHandler
        level=DEBUG
        formatter=simpleFormatter
        args=('/tmp/1.txt', 'a', 10*1024*1024, 5)
        
        [handler_consoleHandler]
        class=StreamHandler
        level=DEBUG
        formatter=simpleFormatter
        args=(sys.stdout,)
        
        [formatter_simpleFormatter]
        format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
        datefmt=
    '''

if __name__ == '__main__':
    print '1st: 下边的log实际打印不出来，因为没有默认的日志配置' + '*' * 50
    log = logging.getLogger(__name__)
    log.info('a')
    log.debug("b")
    log.error("c")
    
    print '2st: 下边获取一个logger' + '*' * 50
    print '实际上在获取的同时，整个python进程中都可以通过logging.getLogger(__name__)使用其配置'
    import time
    time.sleep(1)
    logger = setup_logger(log_file='/tmp/logger_util_test.log')
    logger.info('info')
    logger.debug('debug')
    logger.error('error')
    print '此时，/tmp/logger_util_test.log 文件中可以看到上述的log信息'
    
    print '3st: 下边获取系统log,查看是否使用了第二步的配置' + '*' * 50
    log = logging.getLogger(__name__)
    log.info('a')
    log.debug("b")
    log.error("c")
    print '此时，/tmp/logger_util_test.log 文件中可以看到上述的log信息'
    
    
    
