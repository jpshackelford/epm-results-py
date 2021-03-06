#!/usr/bin/python

import pytest
from mock import Mock, call

import logging
import redis
import time

from epmresults import SensorsDaemon
from epmresults import EPM

from .conftest import r,fpath

class FakeTest():
    def __init__(self, redis_results, epm, logger):                
        self.rr     = redis_results
        self.epm    = epm
        self.logger = logger        
    
    def run(self):    
        return None

@pytest.fixture()
def yaml_mock():
    return Mock(name='yaml')

@pytest.fixture()
def stream_mock():
    return Mock(return_value=file( fpath('sample_01_device_config.yaml'), 'r'))
    
@pytest.fixture()
def d():
    daemon = SensorsDaemon(redis = r(request=None))
    daemon.epm_yaml_stream = stream_mock()
    return daemon

class TestSensorsDaemon(object):
    
    def test_initialize_system(self,d):
        assert d.rr == None
        d.initialize_system()
        assert d.rr.redis().ping()
        assert isinstance(d.epm, EPM)
        
    def test_run(self, yaml_mock):
        
        redis_mock      = Mock(name='redis_results')
        logging_mock    = Mock(name='logger')
        epm_mock        = Mock(name='epm')
        test_mock       = Mock(name='test_run')
        results_mock    = Mock(name='redis_results')
        
        
        sd = SensorsDaemon(redis         = redis_mock,
                           logger        = logging_mock,
                           epm_class     = epm_mock,
                           test_class    = test_mock,
                           results_class = results_mock,
                           loop_count    = 2)
        
        sd.epm_yaml_stream = yaml_mock
        
        sd.run()
        
        assert epm_mock.mock_calls == [
            call(logging_mock, yaml_mock()),
            call().initialize(),
            call().detect_sensors_ready(),
            call().signal_ready(),
            call().detect_test_start(),
            call().signal_test_complete(),
            call().detect_sensors_ready(),
            call().signal_ready(),
            call().detect_test_start(),
            call().signal_test_complete()
        ]
        
        assert test_mock.mock_calls == [
            call(sd.rr, sd.epm, sd.logger, sd, test_length=600, sleep_secs = 0.001),
            call().run(),
            call(sd.rr, sd.epm, sd.logger, sd, test_length=600, sleep_secs = 0.001),
            call().run()            
        ]
        
    def test_end_to_end(self):
        sd = SensorsDaemon(
            yaml_path = fpath('sample_02_device_config.yaml'),
            namespace = 'fake',
            test_secs = 7,
            loop_count = 1,
            scans_per_sec = 20
        )
        sd.run()
        
        last_test = sd.rr.last_test_name()

        configured_sensors = sd.epm.devcfg.inputs('epm_sensors').keys()
        configured_sensors.sort()

        visited_sensors = list( sd.rr.sensors_visited( last_test ))
        visited_sensors.sort()

        assert visited_sensors == configured_sensors
        
