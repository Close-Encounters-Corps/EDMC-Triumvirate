# coding=utf-8

import sys
import re
import ttk
import Tkinter as tk
import requests
import os
import csv
import json
import uuid
import inspect	
from urllib import quote_plus
from  math import sqrt,pow,trunc
from ttkHyperlinkLabel import HyperlinkLabel
import datetime
import webbrowser
import threading
from winsound import *
import ctypes
import os
from config import config
import myNotebook as nb
from urllib import quote_plus
import requests
import json
import inspect	
import ctypes

from modules import journaldata
from modules import factionkill
from modules import nhss
from modules import codex
from modules import hdreport
from modules import news
from modules import release
from modules import legacy
from modules import clientreport
from modules import fssreports
from modules import patrol
from modules.systems import Systems
from modules.debug import Debug
from modules.debug import debug





import ttk
import Tkinter as tk
import sys
    
this = sys.modules[__name__]

this.nearloc = {
   'Latitude' : None,
   'Longitude' : None,
   'Altitude' : None,
   'Heading' : None,
   'Time' : None
}


myPlugin = "EDMC-Triumvirate"


this.version="1.0.3"
this.client_version="{}.{}".format(myPlugin,this.version)
this.body_name=None
    
def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)
    
    this.news.plugin_prefs(frame, cmdr, is_beta,1)
    this.release.plugin_prefs(frame, cmdr, is_beta,2)
    this.patrol.plugin_prefs(frame, cmdr, is_beta,3)
    Debug.plugin_prefs(frame,this.client_version,4)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta,5)
    hdreport.HDInspector(frame,cmdr, is_beta,this.client_version,6)
    
    
    
    return frame

    
def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    this.news.prefs_changed(cmdr, is_beta)
    this.release.prefs_changed(cmdr, is_beta)
    this.patrol.prefs_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    Debug.prefs_changed()
 

#def plugin_dir():
#    buf = ctypes.create_unicode_buffer(1024)
#    ctypes.windll.kernel32.GetEnvironmentVariableW(u"USERPROFILE", buf, 1024)
#    home_dir = buf.value
#    plugin_base = os.path.basename(os.path.dirname(__file__))
#    return home_dir+'\\AppData\\Local\\EDMarketConnector\\plugins\\'+plugin_base



def plugin_start(plugin_dir):
    """
    Load Template plugin into EDMC
    """
    #set a new variable
    #goodPluginDir = plugin_dir()

    #then use it
    release.Release.plugin_start(plugin_dir)
    Debug.setClient(this.client_version)
    patrol.CanonnPatrol.plugin_start(plugin_dir)
    codex.CodexTypes.plugin_start(plugin_dir)



    return 'Triumvirate'
    
def plugin_app(parent):

    this.parent = parent
    #create a new frame as a containier for the status
    padx, pady = 10, 5  # formatting
    sticky = tk.EW + tk.N  # full width, stuck to the top
    anchor = tk.NW

    frame = this.frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)

    table = tk.Frame(frame)
    table.columnconfigure(1, weight=1)
    table.grid(sticky="NSEW")
    
    
    this.news = news.CanonnNews(table,0)
    this.release = release.Release(table,this.version,1)
    this.codexcontrol = codex.CodexTypes(table,2)
    this.patrol = patrol.CanonnPatrol(table,2)
    
    
    
    return frame
    
   
def journal_entry(cmdr, is_beta, system, station, entry, state):
    '''
    
    '''
    # capture some stats when we launch not read for that yet
    # startup_stats(cmdr)

    
        
    if ('Body' in entry):
            this.body_name = entry['Body']        
        
    if system:
        x,y,z=Systems.edsmGetSystem(system)
    else:
        x=None
        y=None
        z=None    
    
    return journal_entry_wrapper(cmdr, is_beta, system, station, entry, state,x,y,z,this.body_name,this.nearloc['Latitude'],this.nearloc['Longitude'],this.client_version)    
    
# Detect journal events
def journal_entry_wrapper(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
    
    factionkill.submit(cmdr, is_beta, system, station, entry,client) #legacyOk
    nhss.submit(cmdr, is_beta, system, station, entry,client) #legacyOk
    hdreport.submit(cmdr, is_beta, system, station, entry,client) #legacyOk
    codex.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client) #legacyOk
    fssreports.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client) #legacyOk
    journaldata.submit(cmdr, is_beta, system, station, entry,client) #k
    clientreport.submit(cmdr,is_beta,client,entry) 
    this.patrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    this.codexcontrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    
    # legacy logging to google sheets
    #legacy.stat(cmdr, is_beta, system, station, entry, state)
    legacy.Stats.statistics(cmdr, is_beta, system, station, entry, state)
    legacy.CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    legacy.fssreports(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client) 
    legacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    legacy.NHSS.submit(cmdr, is_beta, system,x,y,z, station, entry,client)
        
    
def dashboard_entry(cmdr, is_beta, entry):
      
    
    this.landed = entry['Flags'] & 1<<1 and True or False
    this.SCmode = entry['Flags'] & 1<<4 and True or False
    this.SRVmode = entry['Flags'] & 1<<26 and True or False
    this.landed = this.landed or this.SRVmode
      #print "LatLon = {}".format(entry['Flags'] & 1<<21 and True or False)
      #print entry
    if(entry['Flags'] & 1<<21 and True or False):
        if('Latitude' in entry):
            this.nearloc['Latitude'] = entry['Latitude']
            this.nearloc['Longitude'] = entry['Longitude']
    else:
        this.body_name = None
        this.nearloc['Latitude'] = None
        this.nearloc['Longitude'] = None    
    
def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    #debug(json.dumps(data,indent=4))
    this.patrol.cmdr_data(data, is_beta)