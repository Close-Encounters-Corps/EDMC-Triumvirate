from .debug import debug
from .debug import debug,error
import threading
import requests
import sys
import json

try: #py3
    import tkinter as tk
    from tkinter import Frame
    from urllib.parse import quote_plus
except: #py2
    import Tkinter as tk
    from Tkinter import Frame
    from urllib import quote_plus




class whiteListGetter(threading.Thread):
    def __init__(self,callback):
        threading.Thread.__init__(self)
        self.callback = callback

    def run(self):
        debug("getting whiteList")
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/whitelist"
        r = requests.get(url)   
            
        if not r.status_code == requests.codes.ok:
            error("whiteListGetter {} ".format(url))
            error(r.status_code)
            error(r.json())
            results = []
        else:
           results = r.json()
           
        self.callback(results)
        
class whiteListSetter(threading.Thread):

    def __init__(self,cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
        threading.Thread.__init__(self)
        self.cmdr = quote_plus(cmdr.encode('utf8'))
        self.system = quote_plus(system.encode('utf8'))
        self.is_beta = is_beta
        self.station = station
        self.body = body
        self.entry = entry
        self.state = state
        self.x = x
        self.y = y
        self.z = z
        self.lat = lat
        self.lon = lon
        self.client = client
        
    def run(self):
        
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitRaw?"
        url = url + "&cmdrName={}".format(self.cmdr)
        url = url + "&systemName={}".format(self.system)
        url = url + "&bodyName={}".format(self.body)
        url = url + "&station={}".format(self.station)
        url = url + "&event={}".format(self.entry.get("event"))
        url = url + "&x={}".format(self.x)
        url = url + "&y={}".format(self.y)        
        url = url + "&z={}".format(self.z)        
        url = url + "&lat={}".format(self.lat)        
        url = url + "&lon={}".format(self.lon)        
        url = url + "&is_beta={}".format(self.is_beta)        
        url = url + "&raw_event={}".format(quote_plus(json.dumps(self.entry, ensure_ascii=False).encode('utf8')))
        url = url + "&clientVersion={}".format(self.client)
        
        r = requests.get(url)
            
        if not r.status_code == requests.codes.ok:
            error("whiteListSetter {} ".format(url))
            error(r.status_code)
            error(r.json())
            results = []
        else:
           results = r.json()
           
        
        
'''
  Going to declare this aa a frame so I can run a time
'''        
class whiteList(Frame):

    whitelist = []

    def __init__(self, parent):
        Frame.__init__(
            self,
            parent
        )
     
    '''
        if all the keys match then return true
    '''    
    @classmethod
    def matchkeys(cls,event,entry):
        
        ev = json.loads(event)
        for key in ev.keys():
            if not entry.get(key) == ev.get(key):
                return False
         
        return True
        
    @classmethod 
    def journal_entry(cls,cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
               
        for event in whiteList.whitelist:
           
            if cls.matchkeys(event.get("definition"),entry):
                debug("Match {}".format(entry.get("event")))
                whiteListSetter(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client).start()
            
    
    '''
      We will fetch the whitelist on the hour
    '''
    
    def fetchData(self):
        whiteListGetter(self.whiteListCallback).start()
        self.after(1000 * 60 * 60,self.fetchData)
        
 
    def whiteListCallback(self,data):
        whiteList.whitelist = data
        