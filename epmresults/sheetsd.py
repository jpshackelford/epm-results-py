# 
#  Update the Google Spreadsheet from 
#  test data collected in Redis.
#
#  Some of this content from Google's
#  Python Quick Start.
#
from __future__ import print_function

import logging

from logging.handlers import SysLogHandler
from service import find_syslog, Service

import redis 
import httplib2
import os
import time

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from epmresults import RedisResults
    
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-sheetsd.json
SCOPES             = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME   = 'evm_sheetsd Elevated Plus Maze Sheets Daemon'
EPM_SHEET_ID       = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'



class SheetsDaemon(Service):
    
    def __init__(self, **kwargs):        
        
        r = kwargs.pop('redis', None)
        if r:
            self.rr = RedisResults(redis=r)
        else:
            self.rr = RedisResults()
            
        super(SheetsDaemon,self).__init__('sheetsd',**kwargs)        
        self.logger.addHandler(SysLogHandler(address=find_syslog(),
                               facility=SysLogHandler.LOG_DAEMON))
        self.logger.setLevel(logging.INFO)
        
        

    def run(self):
        self.logger.info("sheetsd service started")        
        while not self.got_sigterm():
            self.sync_all()
            time.sleep(1)
        self.logger.info("sheetsd service stopped")

    
    def is_test_complete(self,test_name):
        return True    
        
    def spreadsheetId():
        return EPM_SHEET_ID

    def tab_names(self):
        # Returns an array of tabs in the spreadsheet
        return []

    def redis_test_set(self):
        # Returns an array of completed tests from Redis.
        return []

    def create_test_sheet(self,test_name):
        self.logger.debug("Adding new tab for %s. " % test_name)
        
        self.logger.debug("Added new tab for %s " % test_name)
        return True

    def sync_all(self):
        for test in enumerate( self.unsynced_tests() ): 
            self.sync_test_results(test)
        
    def sync_test_results(self,test_name):        
        self.logger.debug("Syncing tab for %s. " % test_name)        

        if not(test_name in tab_names()):
            create_test_sheet(test_name)
        
        self.logger.debug("Syncing tab for %s. " % test_name)
        
        if is_test_complete(test_name):
            self.rr.mark_as_synced(test_name)
            
        return True
    
    def redis_test_results(self):
        return []

    def parse_redis_entry(self,string):
        # Converts string entry in Redis into the separate
        # for inserting into the Google spreadsheet correcting
        # data types
        return []

    def update_summary_tab(self,test_name):
        return True

    def service(self):
        # Returns API service object.
        
        if not SERVICE:
            credentials = get_credentials()
            http = credentials.authorize(httplib2.Http())
            discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                            'version=v4')
            SERVICE = discovery.build('sheets', 'v4', http=http,
                                      discoveryServiceUrl=discoveryUrl)
        return SERVICE
        

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'sheets.googleapis.com-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials


if __name__ == '__main__':
    import sys

    service_name = sys.argv[0]
    
    if len(sys.argv) != 2:
        sys.exit('Syntax: %s COMMAND' % service_name)

    cmd = sys.argv[1].lower()
    daemon = SheetsDaemon(service_name, pid_dir='/tmp')

    if cmd == 'start':
        daemon.start()
    elif cmd == 'stop':
        daemon.stop()
    elif cmd == 'status':
        if daemon.is_running():
            print('%s is running.' % service_name)
        else:
            print('%s is not running.' % service_name)
    else:
        sys.exit('Unknown command "%s".' % cmd)
