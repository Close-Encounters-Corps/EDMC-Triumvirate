﻿import threading
import requests
import sys
import json
from .emitter import Emitter
try: #py3
    from urllib.parse import quote_plus
    import  urllib.parse as urlparse
except:#py2
    from urllib import quote_plus
    import urllib as urlparse
from .debug import debug,error
from .systems import Systems
import random
import time


class fssEmitter(Emitter):
    types = {}
    reporttypes = {}
    excludefss = {}
    fssFlag = False


    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
        Emitter.__init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
        self.modelreport = "xxreports"
        self.modeltype = "xxtypes"


class fssEmitter(Emitter):
    types={}
    reporttypes={}
    excludefss={}
    fssFlag=False
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        Emitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="xxreports"
        self.modeltype="xxtypes"
        
    def getFssPayload(self):
        payload=self.setPayload()
        payload["reportStatus"]="pending"
        payload["systemAddress"]=self.entry.get("SystemAddress")
        payload["signalName"]=self.entry.get("SignalName")
        payload["signalNameLocalised"]=self.entry.get("SignalName_Localised")
        
        payload["spawningState"]=self.entry.get("SpawningState")
        payload["spawningStateLocalised"]=self.entry.get("SpawningState_Localised")
        payload["spawningFaction"]=self.entry.get("SpawningFaction")
        
        payload["rawJson"]=self.entry
            
        return payload           
        
    def getLcPayload(self):
        payload=self.setPayload ()
        payload["reportStatus"]="pending"
        payload["systemAddress"]=self.entry.get("SystemAddress")
        payload["signalName"]=self.entry.get("SignalName")
        payload["signalNameLocalised"]=self.entry.get("SignalName_Localised")
        
        
        debug(payload)
        
        payload["rawJson"]=self.entry
            
        return payload                   
        
    def getAXPayload(self):
        payload=self.setPayload()
        payload["reportStatus"]="pending"
        payload["systemAddress"]=self.entry.get("SystemAddress")
        #can remove these from strapi model because they will always be the same
        #payload["signalName"]=self.entry.get("signalName")
        #payload["signalNameLocalised"]=self.entry.get("signalNameLocalised")
        payload["rawJson"]=self.entry
        
        return payload                   
                
    def gSubmitAXCZ(self,payload):
        p=payload.copy()
        p["x"],p["y"],p["z"]=Systems.edsmGetSystem(payload.get("systemName"))
        if p.get("isBeta"):
            p["isBeta"]='Y'
        else:
            p["isBeta"]='N'
           
        p["rawJson"]=json.dumps(payload.get("rawJson"), ensure_ascii=False).encode('utf8')
        
        url="https://us-central1-canonn-api-236217.cloudfunctions.net/submitAXCZ"
        debug("gSubmitAXCZ {}".format(p.get("systemName")))
        
        getstr="{}?{}".format(url,urlparse.urlencode(p))
        
        debug("gsubmit {}".format(getstr))
        r=requests.get(getstr)
        
        if not r.status_code == requests.codes.ok:
            error(getstr)
            error(r.status_code)
            
        
                
    def getExcluded(self):

        # sleep a random amount of time to avoid race conditions
        timeDelay = random.randrange(1, 100)
        time.sleep(1/timeDelay)
        if not fssEmitter.fssFlag:
            fssEmitter.fssFlag=True
            debug("Getting FSS exclusions")
            r=requests.get("{}/excludefsses?_limit=1000".format(self.getUrl()))
            debug("{}/excludefsses?_limit=1000".format(self.getUrl()))
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    fssEmitter.excludefss[exc.get("fssName")]=True
            else:
                debug("FFS exclusion failed")
                debug("status: {}".format(r.status_code))
                    
    def run(self):
        
        self.getExcluded()
        
        # is this a code entry and do we want to record it?
        # We dont want o record any that don't begin with $ and and with ;
        if self.entry["event"] == "FSSSignalDiscovered" and not fssEmitter.excludefss.get(self.entry.get("SignalName")) and not self.entry.get("SignalName") == "$USS;" and not self.entry.get("IsStation") and '$' in self.entry.get("SignalName"):
            
            url=self.getUrl()
            
            if  "$Warzone_TG" in self.entry.get("SignalName"):
                payload=self.getAXPayload()
                self.gSubmitAXCZ(payload)
                self.modelreport="axczfssreports"
            elif "$Fixed_Event_Life_Cloud" in self.entry.get("SignalName"):
                debug("Life Cloud")
                payload=self.getLcPayload()
                self.modelreport="lcfssreports"
            else: 
                payload=self.getFssPayload()
                self.modelreport="reportfsses"
            
            self.send(payload,url)

def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    fssEmitter(cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client).start()   
