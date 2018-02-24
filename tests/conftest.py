import pytest
import redis
import os

from mock import Mock

def _get_client(cls, request=None, **kwargs):
    params = {'host': 'localhost', 'port': 6379, 'db': 9}
    params.update(kwargs)
    client = cls(**params)
    client.flushdb()
    if request:
        def teardown():
            client.flushdb()
            client.connection_pool.disconnect()
        request.addfinalizer(teardown)
    return client

@pytest.fixture()
def r(request, **kwargs):
    return _get_client(redis.StrictRedis, request, **kwargs)

def fpath(fname):
    return os.path.join(os.path.dirname(__file__), fname)

