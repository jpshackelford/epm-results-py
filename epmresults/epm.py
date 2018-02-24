import time
from epmresults import DeviceConfig, InputPin, OutputPin, Pin

class EPM(object):
    
    def __init__(self, logger, yaml):
        self.logger = logger
        self.devcfg = DeviceConfig(yaml)

    def initialize(self):
        self.devcfg.initialize()
    
    def read_sensors(self):
        return self.devcfg.input_values('epm_sensors', values=False)

    def detect_test_start(self):
        while (self.test_start_triggered() == False):
            time.sleep(0.01)

    def test_start_triggered(self):
        return len(self.devcfg.input_values('test_trigger', values=False)) > 0
        
    def signal_ready(self):
        self.logger.info("ready to start next test")
    
    def signal_recording(self):
        self.logger.info("test in-progress")
        
    def signal_prepare_to_stop(self):
        self.logger.info("prepare to stop test")
        
    def signal_test_complete(self):
        self.logger.info("test complete")
        