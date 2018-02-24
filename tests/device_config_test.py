#!/usr/bin/python
import pytest
from mock import Mock, call

import pyaml, yaml
import os

import Adafruit_GPIO as GPIO

from epmresults import DeviceConfig, DeviceConfigError, Pin, InputPin, OutputPin


def fpath(fname):
    return os.path.join(os.path.dirname(__file__), fname)
        
@pytest.fixture()
def dc(yaml1):
    stream = file( fpath('sample_01_device_config.yaml'), 'r')
    return DeviceConfig(stream)

@pytest.fixture()
def yaml1():
    stream = file( fpath('sample_01_device_config.yaml'), 'r')
    return yaml.load(stream)

class TestPin(object):
    
    def test_pin(self):
        p = Pin(Mock(),pin=1,name='test')
        assert p.pin()  == 1 
        assert p['pin'] == 1
        assert p.name() == 'test'
        assert p['name'] == 'test'

    def test_str(self):
        device = Mock()
        assert str( Pin(device, pin=1)) == str(Pin(device, pin=1))
        
    def test_equality(self):
        device = Mock()
        assert Pin(device, pin=1) == Pin(device, pin=1)
        assert Pin(device, pin=1) != Pin(device, pin=2)
       
class TestDeviceConfig(object):
    
    def test_sample_yaml(self,yaml1):
        assert sorted(yaml1.keys()) == ['construct','import','input','output']
    
    def test_initialize_devices(self,dc,yaml1):
        dc.initialize_devices(yaml1)
        devices = dc.devices.keys()
        assert sorted(devices) == ['MCP1','MCP2','Pi']
        mcp1 = dc.device('MCP1')
        assert isinstance(mcp1, Mock)
    
    def test_initialize_input_pins(self,dc,yaml1):
        device_mock = Mock(name='device')
        dc.device = Mock(return_value=device_mock)
        dc.initialize_input_pins(yaml1)
        
        assert len(dc.inputs('epm_sensors')) == 2
        assert len(dc.inputs()) == 3
        
        pin1 = dc.inputs('epm_sensors')['Open Arm|-9']
        assert isinstance(pin1,InputPin)
        assert pin1.device() == device_mock
        assert pin1['pullup'] == True
        assert pin1.name() == 'Open Arm|-9'


    def test_initialize_input_pins_no_device(self,dc,yaml1):
        device_mock = Mock(name='device')
        dc.device = Mock(return_value=device_mock)
        
        del yaml1['input']['epm_sensors']['Open Arm|-9']['device']
        with pytest.raises(DeviceConfigError):
            dc.initialize_input_pins(yaml1)
 

    def test_initialize_output_pins(self,dc,yaml1):
        device_mock = Mock(name='device')
        dc.device = Mock(return_value=device_mock)
        dc.initialize_output_pins(yaml1)
        
        assert len(dc.outputs('leds')) == 1
        assert len(dc.outputs()) == 3
        
        pin1 = dc.outputs('buzzers')['Buzzer-2']
        assert isinstance(pin1,OutputPin)
        assert pin1.device() == device_mock
        assert pin1.name() == 'Buzzer-2'
        
        
    def test_configure_pins(self,dc,yaml1):
        device_mock = Mock(name='device')
        dc.device = Mock(return_value=device_mock)
        dc.initialize_input_pins(yaml1)
        dc.initialize_output_pins(yaml1)
        dc.configure_pins()
        
        assert device_mock.mock_calls == [
            call.setup(1, GPIO.IN),
            call.pullup(1, True),
            call.setup(2, GPIO.IN),
            call.pullup(2, True),
            call.setup(3, GPIO.IN),
            call.setup(5, GPIO.OUT),
            call.setup(4, GPIO.OUT),
            call.setup(6, GPIO.OUT)
        ]

    def test_inputs_with_group(self,dc,yaml1):
        mcp1 = Mock(name='MCP1')
        mcp2 = Mock(name='MCP2')
        dc.devices = {'MCP1': mcp1, 'MCP2': mcp2}
        dc.initialize_input_pins(yaml1)
        assert dc.inputs('epm_sensors') == \
            {'Open Arm|-9': InputPin(device=mcp1, pin=1),
             'Open Arm|-8': InputPin(device=mcp2, pin=2) }
    
    def test_inputs_with_group_that_doesnt_exist(self,dc,yaml1):
        mcp1 = Mock(name='MCP1')
        mcp2 = Mock(name='MCP2')
        dc.devices = {'MCP1': mcp1, 'MCP2': mcp2}
        dc.initialize_input_pins(yaml1)
        assert dc.inputs('nonsuch') == {}

    def test_input_values_true(self, dc):
        dc.initialize()
        mcp1 = dc.devices['MCP1']
        mcp2 = dc.devices['MCP2']
        mcp1.input = Mock(return_value = True)
        mcp2.input = Mock(return_value = False)
        results = dc.input_values()
        mcp1.assert_has_calls([ call.input(1) ])
        mcp2.assert_has_calls([ call.input(2), call.input(3) ])
        assert results == {'Open Arm|-9' : InputPin(device=mcp1,pin=1)}

    def test_input_values_false(self, dc):
        dc.initialize()
        mcp1 = dc.devices['MCP1']
        mcp2 = dc.devices['MCP2']
        mcp1.input = Mock(return_value = True)
        mcp2.input = Mock(return_value = False)
        results = dc.input_values(values=False)
        mcp1.assert_has_calls([ call.input(1) ])
        mcp2.assert_has_calls([ call.input(2), call.input(3) ])
        assert results == {'Open Arm|-8'  : InputPin(device=mcp2, pin=2),
                           'Reset Button' : InputPin(device=mcp2, pin=3 ) }

    def test_flatten(self,dc):
        device = Mock()
        dict1 = { 'key1' : {'a': Pin(device, pin=1),
                            'b': Pin(device, pin=2)},
                  'key2' : {'c': Pin(device, pin=3),
                            'd': Pin(device, pin=4)}
                 }
        dict2 = dc.flatten(dict1)
        assert dict2 ==  { 'a' : Pin(device, pin=1),
                           'b' : Pin(device, pin=2),
                           'c' : Pin(device, pin=3),
                           'd' : Pin(device, pin=4) }
