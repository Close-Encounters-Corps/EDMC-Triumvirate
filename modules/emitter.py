# -*- coding: utf-8 -*-
import threading
import requests
import sys
import json
from .debug import Debug
from .debug import debug,error
from .lib.context import global_context
from .release import Release, Environment

class postJson(threading.Thread):
    def __init__(self, url,payload):
        threading.Thread.__init__(self)
        self.url = url
        self.payload = payload

    def run(self):
        debug("emitter.post")

        r = requests.post(self.url, data=json.dumps(self.payload, ensure_ascii=False).encode('utf8'),
        headers={"content-type": "application/json"})
        if not r.status_code == requests.codes.ok:
            error(json.dumps(self.payload))
            error(r.status_code)
            error(r.json())
        else:
            debug("emitter.post success")
            debug(json.dumps(r.json(),indent=4))
            
def post(url,payload):
    postJson(url,payload).start()            


def get_endpoint(is_beta=False):
    urls = {
        Environment.LIVE: "https://api.canonn.tech:2053",
        Environment.STAGING: "https://api.canonn.tech:2053",
        Environment.DEVELOPMENT:  "https://api.canonn.tech:2083"
    }
    if is_beta:
        return urls[Environment.STAGING]
    env = env = global_context.by_class(Release).env
    return urls[env]

class Emitter(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''

    route = ""    
        
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        threading.Thread.__init__(self)
        self.cmdr = cmdr
        self.system = system
        self.x = x
        self.y = y
        self.z = z
        self.body = body
        self.lat = lat
        self.lon = lon
        self.is_beta = is_beta
        if entry:
            self.entry = entry.copy()
        self.client = client
        Emitter.setRoute(is_beta,client)
        self.modelreport = "clientreports"

    @classmethod
    def setRoute(cls,is_beta,client):
        if Emitter.route:
            return Emitter.route
        else:
            endpoint = get_endpoint()
            Emitter.route = endpoint
            
            r = requests.get("{}/clientroutes?clientVersion={}".format(endpoint, client))
            j = r.json()
            if not r.ok or not j:
                debug("Using {}".format(Emitter.route))
            else:   
                Emitter.route = j[0].get("route")
                debug("Route override to {}".format(Emitter.route))
                
        return Emitter.route

        
    def getUrl(self):
        return get_endpoint(self.is_beta)
        
    def setPayload(self):
        payload = {}
        payload["cmdrName"] = self.cmdr  
        payload["systemName"] = self.system
        payload["isBeta"] = self.is_beta
        payload["clientVersion"] = self.client
        return payload   
    
    def run(self):
    
        #configure the payload
        payload = self.setPayload()
        url = self.getUrl()
        self.send(payload,url)
    
    def send(self,payload,url):
        fullurl = "{}/{}".format(url,self.modelreport)
        r = requests.post(fullurl,data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),headers={"content-type":"application/json"})  
        
        if not r.ok:
            error("{}/{}".format(url,self.modelreport))
            error(r.status_code)
            headers = r.headers
            contentType = str(headers['content-type'])
            content=(r.content.decode("utf-8"))
            error(contentType)
            if 'json' in contentType:
                error(json.dumps(content))
            else:
                if "Offline for Maintenance" in str(r.content):
                    error("Canonn API Offline")
                else:
                    error(content)
            error(json.dumps(payload))
        else:
            debug("{}?id={}".format(fullurl,r.json().get("id")))


            


            
