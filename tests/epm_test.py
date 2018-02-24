import pytest
import time
from mock import Mock, call
from threading import Thread

from epmresults import EPM, InputPin

from .conftest import r,fpath

@pytest.fixture()
def yaml_stream():
    return file(fpath('sample_01_device_config.yaml'), 'r')

@pytest.fixture()
def loggr():
    return Mock(name='logger')

@pytest.fixture()
def epm():
    e = EPM( loggr(), yaml_stream())
    e.initialize()
    return e


class TestEPM(object):
    def test_fixtures(self, epm):
        assert epm.devcfg.devices.keys() == ['MCP1', 'MCP2', 'Pi']  
        assert isinstance(epm.devcfg.devices['MCP1'] , Mock)
        assert isinstance(epm.devcfg.devices['MCP2'] , Mock)
        assert isinstance(epm.devcfg.devices['Pi'] , Mock)
        
    def test_read_sensors(self, epm):
        mcp1 = epm.devcfg.devices['MCP1']
        mcp2 = epm.devcfg.devices['MCP2']
        mcp1.input = Mock(return_value = False)
        mcp2.input = Mock(return_value = True)
        results = epm.read_sensors()
        mcp1.assert_has_calls([ call.input(1) ])
        mcp2.assert_has_calls([ call.input(2) ])
        assert results == {'Open Arm|-9'  : InputPin(device=mcp1, pin=1)}

    
    def test_read_sensors_from_correct_group(self, epm):
        epm.devcfg = Mock('DeviceConfig')
        epm.devcfg.input_values = Mock(return_value = {})
        epm.read_sensors()
        epm.devcfg.input_values.assert_called_with('epm_sensors', values=False)

    def test_test_start_triggered_from_correct_group(self, epm):
        epm.devcfg = Mock('DeviceConfig')
        epm.devcfg.input_values = Mock(return_value={})
        epm.test_start_triggered()
        epm.devcfg.input_values.assert_called_with('test_trigger', values=False)

    def test_test_start_triggered(self,epm):
        mcp1 = epm.devcfg.devices['MCP1']
        mcp1.input = Mock(return_value = True)
        assert epm.test_start_triggered() == False
        mcp1.input = Mock(return_value = False)
        assert epm.test_start_triggered() == True
        assert mcp1.mock_calls == [call.setup(1, 1), call.pullup(1, True), call.input(1), call.input(1)]
        
    def test_detect_test_start_blocks(self,epm):
        mcp1 = epm.devcfg.devices['MCP1']
        mcp1.input = Mock(return_value = True)
        SignalAfterDelay(mcp1).start() # sets mcp1.input = Mock(return_value = False)
        epm.detect_test_start()
        assert mcp1.mock_calls.count( call.input(1) ) > 3

class SignalAfterDelay(Thread):

    def __init__(self, device_mock):
        Thread.__init__(self)
        self.device_mock = device_mock

    def run(self):
        time.sleep(0.1)
        self.device_mock.input = Mock(return_value = False)
