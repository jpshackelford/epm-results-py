import pytest
from mock import Mock, patch, call

import time

from epmresults import SingleTestRun, EPM, InputPin

from .conftest import r

@pytest.fixture()
def rr():
    res = Mock(name = 'redis_results')
    res.is_aborted = Mock(return_value = False)
    return res

@pytest.fixture()
def epm():
    d = Mock(name='device')
    e = Mock(name = 'epm')
    e.read_sensors = Mock(side_effect=[
            {'A': InputPin(d,pin=1) },
            {'B': InputPin(d,pin=2) },
            {'C': InputPin(d,pin=3) },
            {'D': InputPin(d,pin=4), 
             'E': InputPin(d,pin=5) },
            {'F': InputPin(d,pin=6) }
    ])
    return e

@pytest.fixture()
def log():
    return Mock(name = 'logger')

@pytest.fixture()
def daemon():
    d = Mock(name = 'daemon')
    d.got_sigterm = Mock(return_value=False)
    return d

@pytest.fixture()
def t(rr,epm,log,daemon,test_len=1.0,sleep_secs=0.1):
    trun = SingleTestRun( rr, epm, log, daemon,
                          test_length = test_len,
                          sleep_secs  = sleep_secs)
    return trun


class TestSingleTestRun(object):
    
    def test_consruction(self,t,rr,epm,log,daemon):
        assert t.rr     == rr
        assert t.epm    == epm
        assert t.logger == log
        assert t.daemon == daemon
        
    def test_run(self,t,epm,rr):
        t.remaining_time = Mock(side_effect = [1,0,0,0])
        t.run()
        assert rr.mock_calls  == [call.start_test(),                                  
                                  call.record_position('A', 0.0, 0.1),
                                  call.is_aborted(),
                                  call.complete_test()]
        
        assert epm.mock_calls == [call.signal_recording(),
                                  call.read_sensors(),
                                  call.signal_prepare_to_stop()]
    
    def test_remaining_time(self,t):
        t.test_length = 60.0
        t.now = Mock(side_effect = [0.0,15.0])
        t.start_timer()
        assert t.remaining_time() == 45.0
        
    def test_new_position_at_start(self,t):
        assert t.new_position(['A','B','C']) == 'A'

    def test_new_position_no_movement(self,t):
        t.recent_pos = ['A','B']
        assert t.new_position(['A','B','C']) == False
        # Note that in case of multiple readings,
        # some of which are recent, we assume no movement.
    
    def test_new_position_movement(self,t):
        t.recent_pos = ['A','B']
        assert t.new_position(['C']) == 'C'
    
    def test_test_seconds(self,t):        
        t.now = Mock(side_effect = [100,100,105,110])
        t.start_timer()
        assert t.test_seconds() == 0
        assert t.test_seconds() == 5
        assert t.test_seconds() == 10
        
    def test_register_position(self,t,rr):        
        t.test_seconds = Mock(side_effect = [0,5,10,15])
        t.register_position('A')
        t.register_position('B')
        t.register_position('C')
        assert t.recent_pos == ['A','B','C']
        assert rr.mock_calls == [ call.record_position('A', 0, 5),
                                  call.record_position('B', 5, 10) ]
        t.complete_test()
        assert rr.mock_calls == [ call.record_position('A', 0, 5),
                                  call.record_position('B', 5, 10),
                                  call.record_position('C',10, 15),
                                  call.is_aborted(),
                                  call.complete_test() ]

