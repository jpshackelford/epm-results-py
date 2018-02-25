import time

from datetime import datetime, timedelta
from pytz import timezone

from epmresults import RedisResults

class Position(object):
    def __init__(self, sensor, start_time, end_time = None):
        self.sensor     = sensor
        self.start_time = start_time
        self.end_time   = end_time
    
class SingleTestRun(object):
    
    def __init__(self, redis_results, epm, logger, daemon, test_length=600, sleep_secs=0.001):                
        self.rr               = redis_results
        self.epm              = epm
        self.logger           = logger
        self.daemon           = daemon
        self.test_length      = test_length
        self.sleep_secs       = sleep_secs
        self.recent_pos       = []
        self.positions        = []
        self.test_aborted     = False
        self.start_time       = None
        
    def run(self):
        self.start_timer()
        self.rr.start_test()
        self.epm.signal_recording()
        while(self.remaining_time() > 0 and not self.test_aborted):            
            positions = self.epm.read_sensors().keys()
            new_pos   = self.new_position(positions)
            if new_pos:
                self.register_position(new_pos)
            
            if self.daemon.got_sigterm():
                self.test_aborted = True
                self.rr.abort_test()
            
            if self.remaining_time() < 15:
                self.epm.signal_prepare_to_stop()
                        
            time.sleep(self.sleep_secs)
                
        self.complete_test()
    
    def start_timer(self):
        self.start_time = self.now()
        return self.start_time
        
    def now(self):
        return time.time()
    
    def test_seconds(self):
        if not self.start_time:
            return None
        else:
            secs = self.now() - self.start_time
            return round(secs, 1)
        
    def remaining_time(self):
        secs = (self.start_time + self.test_length) - self.now()  
        return round(secs, 1)
    
    def register_position(self, sensor):
        t = self.test_seconds()
        
        if len(self.positions) > 0:
            p = self.positions[-1]
            p.end_time = t
            self.rr.record_position(p.sensor, p.start_time, p.end_time)
                
        self.positions.append( Position(sensor, start_time = t) )
        self.recent_pos.append(sensor)
        return sensor
    
    def new_position(self, positions):
        if(len(positions) == 0):
            new_pos = False
        elif len(self.recent_pos) > 0:
            last_pos = self.recent_pos[-1]
            if last_pos in positions: new_pos = False
            else: new_pos = positions[0]
        else:
            new_pos = positions[0]                    
        return new_pos
    
    def complete_test(self):
        if len(self.positions) > 0:
            self.register_position(self.positions[-1].sensor)
        if not self.rr.is_aborted(): self.rr.complete_test()        
