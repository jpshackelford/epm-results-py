import time

class FakeDevice(object):
    
    def __init__(self):
        self.input_vals = None

    def setup(self, pin, purpose):
        return None

    def pullup(self, pin, purpose):
        return None

    def input(self, pin):
        if self.input_vals == None or self.remaining_input_count() < 1:
            self.init_input_matrix()
        return self.input_vals[pin].pop(0)

    def output(self, pin, value):
        return None

    def init_input_matrix(self):
        if self.input_vals == None:
            self.input_vals = {} 
            for i in range(36): self.input_vals[i] = []
            self.add_all_pins_on()
            self.add_all_pins_on()
            self.add_off_for_pin(0)
        
        for i in range(36): 
            self.add_all_pins_on()
            self.add_off_for_pin(i)

    def remaining_input_count(self):    
        min = len(self.input_vals[0])
        if min > 0:
            for i in range(36): 
                lmin = len(self.input_vals[i])
                if min > lmin: min = lmin
        return min

    def add_all_pins_on(self):
        for i in range(36): 
            self.input_vals[i].append(1)

    def add_off_for_pin(self, pin):
        for i in range(36):
            if i == pin: self.input_vals[i].append(0)
            else:  self.input_vals[i].append(1)     
    