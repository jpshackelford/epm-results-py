import Adafruit_GPIO as GPIO
import importlib
import pyaml, yaml

class Pin(object):
    
    def __init__(self,device,**kwargs):
        self.h        = kwargs
        self.d        = device
    
    def name(self):
        return self.h['name']

    def pin(self):
        return int(self.h['pin'])
                   
    def device(self):
        return self.d
    
    def use(self):
        return 'unconfigured'
    
    def __getitem__(self,key):
        return self.h[key]
    
    def __eq__(self, other):
        return isinstance(self, other.__class__) and \
               self.device() == other.device() and \
               self.pin()    == other.pin() and \
               self.use()    == other.use()
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return str(self.__class__.__name__) + \
               ' ' + str(self.pin()) + \
               ' ' + str(self.use()) + \
               ' device: ' + str(self.device())

    def __rep__(self):
        return self.__str__(self)
        
class InputPin(Pin):
    
    def initialize(self):
        self.device().setup(self.pin(), GPIO.IN)
        if 'pullup' in self.h:
            self.device().pullup(self.pin(), bool(self.h['pullup']))

    def input(self):
        return self.device().input(self.pin())
    
    def use(self):
        return 'input'
        
class OutputPin(Pin):
    
    def initialize(self):
        self.device().setup(self.pin(), GPIO.OUT)
        if 'pullup' in self.h:
            self.device().pullup(self.pin(), bool(self.h['pullup']))
    
    def output(self, value):
        self.device().output(self.pin(), value)
        
    def use(self):
        return 'output'

class DeviceConfigError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class DeviceConfig(object):
    
    def __init__(self, yaml):
        self.yaml_source   = yaml
        self._inputs        = {}
        self._outputs       = {}
        self.devices         = {}
        
    def initialize(self):
        y = yaml.load(self.yaml_source)
        self.initialize_devices(y)
        self.initialize_input_pins(y)        
        self.initialize_output_pins(y)
        self.configure_pins()
        
    def initialize_devices(self, y):
        for g,lib in y['import'].iteritems():
            mod, cls = lib.rsplit('.', 1)
            globals()[mod] = importlib.import_module(mod)
            globals()[g]   = eval(lib)
        for key, constructor in y['construct'].iteritems():
            self.devices[key] = eval(constructor)

    def initialize_input_pins(self, y):
        for group, pinset in y['input'].iteritems():
            self._inputs[group] = {}
            for name, p in pinset.iteritems():
                p['name'] = name
                if 'device' in p:
                    d = self.device(p['device'])
                    del p['device']
                else: raise DeviceConfigError("Input pin %s has no device specified." % name)                                   
                self._inputs[group][name] = InputPin(d,**p)
        
    def initialize_output_pins(self, y):
        for group, pinset in y['output'].iteritems():
            self._outputs[group] = {}
            for name, p in pinset.iteritems():
                p['name'] = name
                if 'device' in p:
                    d = self.device(p['device'])
                    del p['device']
                else: raise DeviceConfigError("Output pin %s has no device specified." % name)                                   
                self._outputs[group][name] = OutputPin(d,**p)
    
    def configure_pins(self):
        for p in self.inputs().values(): p.initialize()
        for p in self.outputs().values(): p.initialize()            
        
    def device(self, device_name):
        return self.devices[device_name]
    
    def inputs(self, group=None):
        if group: 
            if group in self._inputs: return self._inputs[group]
            else: return {}
        else:     return self.flatten(self._inputs)
    
    def outputs(self, group=None):
        if group: return self._outputs[group]
        else:     return self.flatten(self._outputs)

    def input_values(self, group=None, values=True):
        results = {}
        for pin in self.inputs(group).values():
            input_val = pin.input()
            if input_val == values:
                results[pin.name()] = pin
        return results

    def flatten(self, groups):
        dict = {}
        for group in groups.values(): dict.update(group)
        return dict
    
    def cleanup(self):
        for p in self.inputs():
            p.output(False)
            p.cleanup
    