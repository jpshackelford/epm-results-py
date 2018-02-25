#
# SensorsDaemon connects EPM sensors to redis datastore.
#
#
import logging

from logging.handlers import SysLogHandler
from service import find_syslog, Service

import os
import time

from epmresults import RedisResults
from epmresults import EPM
from epmresults import SingleTestRun
        
class SensorsDaemon(Service):
    
    def __init__(self, **kwargs):                
        
        self.r                   = kwargs.pop('redis', None)
        self.test_class          = kwargs.pop('test_class', SingleTestRun)
        self.epm_class           = kwargs.pop('epm_class', EPM)
        self.results_class       = kwargs.pop('results_class', RedisResults)
        self.loop_count          = kwargs.pop('loop_count', None)
        self.substitute_logger   = kwargs.pop('logger', None)

        self.yaml_path           = kwargs.pop('yaml_path', '/etc/epm.yaml')
        self.namespace           = kwargs.pop('namespace', None)
        self.test_secs           = kwargs.pop('test_secs', None)
        self.scans_per_sec       = kwargs.pop('scans_per_sec', 1000)
        self.sleep_secs          = kwargs.pop('sleep_secs', 1.0 /self.scans_per_sec)

        super(SensorsDaemon,self).__init__('epmsensorsd',**kwargs)        
        self.logger.addHandler(SysLogHandler(address=find_syslog(),
                               facility=SysLogHandler.LOG_DAEMON))
        self.logger.setLevel(logging.INFO)
        
        if self.substitute_logger: self.logger = self.substitute_logger
        
        self.epm = None
        self.rr  = None

    def run(self):
        self.logger.info("epmsensorsd service started")
        self.initialize_system()
        while(not self.got_sigterm()):
            self.epm.signal_ready()
            self.epm.detect_test_start()
            secs = int(self.test_secs or 600)
            test = self.test_class(self.rr, self.epm, self.logger, self, 
                                   test_length = secs, 
                                   sleep_secs = self.sleep_secs )
            test.run()
            self.epm.signal_test_complete()
            
            # used only for testing
            if self.loop_count: self.loop_count = self.loop_count - 1
            if self.loop_count < 1: break
            
        self.logger.info("epmsensorsd service stopped")        
    
    def initialize_system(self):
        self.logger.info("initializing epm sensors and data collection")                
        self.initialize_redis()
        self.initialize_epm()
    
    def initialize_redis(self):
        if self.r:
            self.rr = self.results_class(redis=self.r)
        else:
            self.rr = self.results_class()
        if self.namespace: self.rr.set_namespace(self.namespace)
        self.rr.redis().ping()
        
    def initialize_epm(self):
        self.logger.info("reading " + self.yaml_path)                        
        self.epm = self.epm_class(self.logger, self.epm_yaml_stream())
        self.epm.initialize()    
    
    def epm_yaml_stream(self):
        return file(self.yaml_path,'r')
    
if __name__ == '__main__':
    import sys

    service_name = sys.argv[0]
    
    if len(sys.argv) != 2:
        sys.exit('Syntax: %s COMMAND' % service_name)

    cmd = sys.argv[1].lower()
    daemon = SensorsDaemon()

    if cmd == 'start':
        daemon.start()
    elif cmd == 'stop':
        daemon.stop()
    elif cmd == 'status':
        if daemon.is_running():
            print('%s is running.' % service_name)
        else:
            print('%s is not running.' % service_name)
    else:
        sys.exit('Unknown command "%s".' % cmd)
