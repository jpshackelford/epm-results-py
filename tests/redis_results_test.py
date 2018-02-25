#!/usr/bin/python

import pytest
from mock import Mock

import redis
from epmresults import RedisResults

from .conftest import r

@pytest.fixture()
def rr():
    return RedisResults(redis= r(request=None))

class TestRedisResults(object):
    
    def test_ping(self, r):
        assert r.ping()
        
    
    def test_namespace(self,rr):
        assert rr.namespace('test_count') == 'epm.test_count'


    def test_fetch_test_count(self,rr,r):
        assert rr.fetch_test_count() == 0        
        assert 'epm.test_count' in r.keys()
        r['epm.test_count'] = 1        
        assert rr.fetch_test_count() == 1


    def test_start_test(self,rr,r):
        with pytest.raises(KeyError):
            r['epm.test_count']
        
        assert rr.start_test() == 1
        assert int(r['epm.test_count']) == 1
        assert 'epm.test_0001.summary' in r.keys()
        assert r.hget('epm.test_0001.summary' ,'test_date')
        
        assert rr.start_test() == 2
        assert int(r['epm.test_count']) == 2
        assert 'epm.test_0002.summary' in r.keys()
        assert r.hget('epm.test_0002.summary' ,'test_date')
        
        
    def test_start_test_adds_unsynced(self,rr,r):
        with pytest.raises(KeyError):
            r['epm.unsynced_tests']
        rr.start_test()
        rr.start_test()
        assert r.smembers('epm.unsynced_tests') == set(['epm.test_0001','epm.test_0002'])
        
    def test_start_test_marks_test_in_progress(self,rr,r):        
        with pytest.raises(KeyError):
            r['epm.test_0001.summary']
        rr.start_test()
        assert r.hget('epm.test_0001.summary','test_state') == 'in-progress'

    def test_complete_test(self,rr,r):        
        r['epm.test_count'] = 3
        r.hget('epm.test_0003.summary','test_state') == 'in-progress'
        rr.complete_test()
        assert r.hget('epm.test_0003.summary','test_state') == 'complete'
    
    def test_abort_test(self,rr,r):        
        r['epm.test_count'] = 3
        r.hget('epm.test_0003.summary','test_state') == 'in-progress'
        rr.abort_test()
        assert r.hget('epm.test_0003.summary','test_state') == 'aborted'
    
    def test_is_aborted(self,rr,r):
        r['epm.test_count'] = 3
        r.hset('epm.test_0003.summary','test_state', 'in-progress')
        assert rr.is_aborted() == False
        r.hset('epm.test_0003.summary','test_state', 'aborted')
        assert rr.is_aborted() == True
        
    def test_record_position(self,rr,r):
        r['epm.test_count'] = 999        
        
        with pytest.raises(KeyError):
            r['epm.test_0999.details']
        
        rr.record_position("Open Arm|-9", 12.345, 67.89)
        rr.record_position("Open Arm|-8", 67.89, 70.0)
        
        assert r.llen('epm.test_0999.details') == 2
        assert r.lindex('epm.test_0999.details',0) == 'Open Arm|-9|12.345|67.89'
        assert r.lindex('epm.test_0999.details',1) == 'Open Arm|-8|67.89|70.0'
        
    def test_unsynced_tests(self,rr,r):
        with pytest.raises(KeyError):
            r['epm.unsynced_tests']
        
        assert rr.unsynced_tests() == set([])
        
        r.sadd('epm.unsynced_tests', 'epm.test_0001')
        r.sadd('epm.unsynced_tests', 'epm.test_0002')        
        assert rr.unsynced_tests() == set(['epm.test_0001','epm.test_0002'])
        
    def test_mark_as_synced(self,rr,r):
        r.sadd('epm.unsynced_tests', 'epm.test_0001')
        r.sadd('epm.unsynced_tests', 'epm.test_0002')
        rr.mark_as_synced('epm.test_0001')
        assert r.smembers('epm.unsynced_tests') == set(['epm.test_0002'])
    
        
