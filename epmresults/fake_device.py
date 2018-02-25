import time

class FakeDevice(object):
    
    def __init__(self):
        self.epm = None
        self._sensor_mask = None
        self.pin_to_signal = 0
        self.input_vals = self.sensor_vals_for_pin(0)

    def setup(self, pin, purpose):
        return None

    def pullup(self, pin, purpose):
        return None

    def input(self, pin):
        if self.input_vals[pin] == None:
            # we are scanning this pin for the second time, so consider this a new scan
            self.pin_to_signal = self.pin_to_signal + 1
            if self.pin_to_signal > 35: self.pin_to_signal = 0
            self.input_vals = self.sensor_vals_for_pin(self.pin_to_signal)
                
        pinval = self.input_vals[pin]
        self.input_vals[pin] = None # we've returned this pin, mark as read for this scan
        return pinval

    def output(self, pin, value):
        return None

    def set_epm(self, epm):
        self.epm = epm

    def sensor_mask(self):
        if self._sensor_mask == None:
            self._sensor_mask = []
            for i in range(36): self._sensor_mask.append(1)
        return self._sensor_mask

    def sensor_vals_for_pin(self, pin):
        vals = []; vals.extend( self.sensor_mask())
        vals[pin] = 0
        return vals

    