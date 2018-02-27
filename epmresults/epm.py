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

    def detect_sensors_ready(self):
        waiting_on = []
        sensors = self.check_all_sensors()
        off_sensor_names = self.sensor_names( sensors[0] )
        on_sensor_names =  self.sensor_names( sensors[1] )
        while len(off_sensor_names) > 0:
         
            new_problem_sensors = set(off_sensor_names) - set(waiting_on)
            new_working_sensors = set(waiting_on) - set(on_sensor_names)

            if len(new_working_sensors) > 0:
                self.logger.info("[epmsensorsd]  The following sensors are now properly ON and ready: ")
                for s in new_working_sensors:
                    self.logger.info("[epmsensorsd]  - " + s ) 
                
            if len(new_problem_sensors) > 0:
                self.logger.info("[epmsensorsd]  Waiting for sensors to be ON and ready: ")
                for s in new_problem_sensors:
                    self.logger.info("[epmsensorsd]  - " + s ) 
            
            waiting_on = []; waiting_on.extend( self.sensor_names( sensors[0] ))
            time.sleep(0.1)
            sensors = self.check_all_sensors()
            off_sensor_names = self.sensor_names( sensors[0] )
            on_sensor_names =  self.sensor_names( sensors[1] )

        self.logger.info("[epmsensorsd]  All " + str(len(on_sensor_names)) + " sensors are now properly ON and ready.")
        return None
    
    def sensor_names(self, pin_list):
        names = []
        for pin in pin_list:
            names.extend(pin.name())
        return names

    def detect_test_start(self):
        while (self.test_start_triggered() == False):
            time.sleep(0.01)

    def check_all_sensors(self):
        results = {1: [], 0: []}
        for pin in self.devcfg.inputs('epm_sensors').values():
            v = pin.input()
            results[v].append(pin)
        return results

    def test_start_triggered(self):
        return len(self.devcfg.input_values('test_trigger', values=False)) > 0
        
    def signal_ready(self):
        self.logger.info("[epmsensorsd]  ready to start next test")
    
    def signal_recording(self):
        self.logger.info("[epmsensorsd]  test in-progress")
        
    def signal_prepare_to_stop(self):
        self.logger.info("[epmsensorsd]  prepare to stop test")
        
    def signal_test_complete(self):
        self.logger.info("[epmsensorsd]  test complete")
        