#!/usr/bin/python

import pytest
from mock import Mock

import redis
#from epmresults import SheetsDaemon
from .conftest import r

#@pytest.fixture()
#def d():
#    return SheetsDaemon(redis = r(request=None))

#class TestSheetsDaemon(object):
#    
#    def test_tab_names(self,d):
#        assert d.tab_names() == []
    
    