# Handles communication with Redis
# for EPM Test results.

from redis import StrictRedis
import time
import sys

from datetime import datetime, timedelta
from pytz import timezone

class RedisResults(object):
    
    def __init__(self, host='localhost', port=6379, db=0,redis=None):
        self._namespace = 'epm'
        if redis:
            self.r = redis
        else:
            self.r = StrictRedis(host=host,port=port,db=db)        
    
    def redis(self):
        return self.r
    
    def set_namespace(self,namespace):
        self._namespace = str(namespace)
    
    def namespace(self,key):
        return self._namespace + "." + key
        
    def test_name(self,test_number):
        return self.namespace('test_') + str(test_number).zfill(4)
        
    def now_str(self):    
        utc = datetime.utcnow().replace(tzinfo=timezone('UTC'),microsecond=0)
        return utc.isoformat()
    
    def fetch_test_count(self):
        redis_count = self.r.get(self.namespace('test_count'))
        if not redis_count:
            self.r.set(self.namespace('test_count'),0)
            count = 0
        else:
            count = int(redis_count)
        return count
        
    def start_test(self):
        old_count = self.fetch_test_count()
        new_count=old_count+1
        self.r.set( self.namespace('test_count'), new_count)    
        self.r.hset( self.test_name(new_count) +'.summary','test_date', self.now_str())
        self.r.hset( self.test_name(new_count) +'.summary','test_state','in-progress')
        self.r.sadd(self.namespace('unsynced_tests'), self.test_name(new_count))
        return new_count
   
    def complete_test(self):
       test_count = self.fetch_test_count()
       self.r.hset( self.test_name(test_count) +'.summary','test_state','complete') 
    
    def abort_test(self):
       test_count = self.fetch_test_count()
       self.r.hset( self.test_name(test_count) +'.summary','test_state','aborted')    
    
    def is_aborted(self):
        test_count = self.fetch_test_count()
        aborted = self.r.hget( self.test_name(test_count) +'.summary','test_state') == 'aborted'
        return aborted
    
    def record_position(self, sensor_name, start_time, end_time):
        test_count = self.fetch_test_count()
        self.r.rpush( self.test_name(test_count) +'.details',
                      sensor_name + '|' +
                      str(start_time) + '|'+
                      str(end_time))
        
        self.r.sadd( self.test_name(test_count) +'.sensors_visited', sensor_name)
        
    def unsynced_tests(self):
        return set(self.r.smembers(self.namespace('unsynced_tests')))
    
    def mark_as_synced(self, test_name):
        self.r.srem(self.namespace('unsynced_tests'), test_name)

    def sensors_visited(self, test):
        return self.r.smembers( str(test) + '.sensors_visited')

    def last_test_name(self):
        return  self.test_name(self.fetch_test_count())

    def test_details(self, test):
        test = {}
        test['name'] = test
        test['log']  = self.r.lrange(str(test) + '.details', 0, -1)
        return test
    
    def destroy_all(self):
        keys = self.r.keys( self._namespace + '*')
        self.r.delete(*keys)
