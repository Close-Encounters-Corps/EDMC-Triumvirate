# -*- coding: utf-8 -*- 
from datetime import datetime
import modules.Discord   as Discord
from config import config
import myNotebook as nb
from urllib import quote_plus
import requests
import json
import webbrowser
from modules import journaldata
from modules import factionkill
from modules import nhss
from modules import codex
from modules import hdreport
from modules import news
from modules import release
from modules import legacy
from modules import legacyCanonn as Clegacy
from modules import clientreport
from modules import fssreports
from modules import patrol
from modules import friendfoe as FF
from modules.systems import Systems
from modules.debug import Debug
from modules.debug import debug
from modules import materialReport
from contextlib import closing
from modules.whitelist import whiteList
import csv
import plug
import modules.Commands     
import ttk
import Tkinter as tk
import sys

from modules import BGS


this = sys.modules[__name__]

import l10n
import functools
_ = functools.partial(l10n.Translations.translate, context=__file__)    

this.nearloc = {
   'Latitude' : None,
   'Longitude' : None,
   'Altitude' : None,
   'Heading' : None,
   'Time' : None
}


myPlugin = 'EDMC-Triumvirate'


this.version='1.1.7'
this.SQNag=0
this.client_version='{}.{}'.format(myPlugin,this.version)
this.body=None
this.body_name=None
this.SysFactionState=None 
this.DistFromStarLS=None
this.Nag=0
this.cmdr_SQID=None    #variable for allegiance check
this.CMDR=None
this.SRVmode,this.Fightermode=False,False
this.old_time=0  
this.fuel=0
this.fuel_cons = 0



def plugin_prefs(parent, cmdr, is_beta):
    '''
    Return a TK Frame for adding to the EDMC settings dialog.
    '''
    
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)
    
    this.news.plugin_prefs(frame, cmdr, is_beta,1)
    this.release.plugin_prefs(frame, cmdr, is_beta,2)
    this.patrol.plugin_prefs(frame, cmdr, is_beta,3)
    Debug.plugin_prefs(frame,this.client_version,4)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta,5)
   
    hdreport.HDInspector(frame,cmdr, is_beta,this.client_version,7)
    #release.versionInSettings(frame, cmdr, is_beta,8)
   # entry=nb.Entry(frame,None)
    nb.Label(frame,text="В случае возникновения проблем с плагином \nили в случае, если Вы поставили неправильное сообщество в гугл форме, \nпишите в личку Дискорда Казаков#4700").grid(row=9,column=0,sticky="NW")
    
    
    
    return frame

    
def prefs_changed(cmdr, is_beta):
    '''
    Save settings.
    '''
    this.news.prefs_changed(cmdr, is_beta)
    this.release.prefs_changed(cmdr, is_beta)
    this.patrol.prefs_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    
    Debug.prefs_changed()
    
SQ=None
def Alegiance_get(CMDR,SQ_old):
    global SQ    
    if CMDR!= this.CMDR:
        debug("Community Check started")
        url="https://docs.google.com/spreadsheets/d/e/2PACX-1vTXE8HCavThmJt1Wshy3GyF2ZJ-264SbNRVucsPUe2rbEgpm-e3tqsX-8K2mwsG4ozBj6qUyOOd4RMe/pub?gid=1832580214&single=true&output=tsv"        
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.iter_lines(), delimiter='\t')
            next(reader)
            
            
            for row in reader:
                
                cmdr,squadron,SQID=row
                
                if cmdr == CMDR:
                    try:
                        SQ=SQID
                        debug("your SQID is "+str(SQ))
                    except:
                        error("Set SQID Failed")
                
        if SQ != None:
            debug("SQ ID IS OK")
            this.CMDR=CMDR
            bgs.SQID_set(SQ)
            Discord.SQID_set(SQ)
            patrol.SQID_set(SQ) #Функция для отправки данных о сквадроне в модули, использовать как шаблон 
            return SQ 
        else: 
            if this.Nag==0:
                debug("SQID need to be instaled")
                
                this.Nag=this.Nag+1

                url="https://docs.google.com/forms/d/e/1FAIpQLSeERKxF6DlrQ3bMqFdceycSlBV0kwkzziIhYD0ctDzrytm8ug/viewform?usp=pp_url"
                url+="&entry.42820869="+quote_plus(CMDR)
                
                Discord.SQID_set("N/A")
                patrol.SQID_set("N/A")
                
                debug("SQID "+str(url))
                webbrowser.open(url)
    else: return      SQ_old


   
def plugin_start(plugin_dir):
    '''
    Load Template plugin into EDMC
    '''
    
    #print this.patrol
    plugin_dir=unicode(plugin_dir)
    release.Release.plugin_start(plugin_dir)
    Debug.setClient(this.client_version)
    patrol.CanonnPatrol.plugin_start(plugin_dir)
    codex.CodexTypes.plugin_start(plugin_dir)
    
    bgs=BGS.BGS()
    return 'Triumvirate-{}'.format(this.version)
    
def plugin_stop():
    '''
    EDMC is closing
    '''
    debug('Stopping the plugin')
    this.patrol.plugin_stop()
    
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
    table.grid(sticky='NSEW')
    
    this.codexcontrol = codex.CodexTypes(table,0)
    this.news = news.CECNews(table,1)
    this.release = release.Release(table,this.version,2)
    this.patrol = patrol.CanonnPatrol(table,3)
    whitelist=whiteList(parent)
    whitelist.fetchData()
    #for plugin in plug.PLUGINS:
    #    debug(str(plugin.name)+str(plugin.get_app)+str(plugin.get_prefs))
    
    
    return frame
    
def Squadronsend(CMDR,entry):
      
        url="https://docs.google.com/spreadsheets/d/e/2PACX-1vTXE8HCavThmJt1Wshy3GyF2ZJ-264SbNRVucsPUe2rbEgpm-e3tqsX-8K2mwsG4ozBj6qUyOOd4RMe/pub?gid=1113444368&single=true&output=tsv"        
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.iter_lines(), delimiter='\t')
            next(reader)
            
            
            for row in reader:
                
                cmdr,squadron=row
                
                if CMDR in row:
                    if entry==squadron:
                        this.SQNag==1
        
        if this.SQNag==0:
            debug("SQName need to be sended")
            url="https://docs.google.com/forms/d/e/1FAIpQLScZvs3MB2AK6pPwFoSCpdaarfAeu_P-ineIhtO1mOPgr09q8A/formResponse?usp=pp_url"
            url+="&entry.558317192="+quote_plus(CMDR)
            url+="&entry.1042067605="+quote_plus(entry)
            this.SQNag=this.Nag+1
            
            legacy.Reporter(url).start()
   
def journal_entry(cmdr, is_beta, system, station, entry, state):
    '''
    
    '''
    # capture some stats when we launch not read for that yet
    startup_stats(cmdr)
    


    

    
    if "SystemFaction" in entry:
        ''' "SystemFaction": { “Name”:"Mob of Eranin", "FactionState":"CivilLiberty" } }'''
        SystemFaction=entry.get("SystemFaction")
        #debug(SystemFaction)
        try:
            this.SysFactionState= SystemFaction["FactionState"]
        except: 
            this.SysFactionState=None
        debug("SysFaction's state is"+str(this.SysFactionState))
    
    if "DistFromStarLS" in entry:
        '''"DistFromStarLS":144.821411'''
        try:
            this.DistFromStarLS=entry.get("DistFromStarLS")
        except:
            this.DistFromStarLS=None
        debug("DistFromStarLS="+str(this.DistFromStarLS))
    
        
        
    if entry.get("event") == "FSDJump":
        Systems.storeSystem(system,entry.get("StarPos"))
        this.DistFromStarLS=None
        this.body = None
        
    if ('Body' in entry):
            this.body = entry['Body']
            debug(this.body)
    
    if entry["event"]=="JoinedSquadron":
        Squadronsend(cmdr,entry["SquadronName"])



    if system: 
        x,y,z=Systems.edsmGetSystem(system)
    else:
        x=None
        y=None
        z=None    
    
    return journal_entry_wrapper(cmdr, is_beta, system,this.SysFactionState,this.DistFromStarLS, station, entry, state,x,y,z,this.body,this.nearloc['Latitude'],this.nearloc['Longitude'],this.client_version)    
    

def journal_entry_wrapper(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client):
    '''
    Detect journal events
    '''
    # Если мне нужен вывод данных из модулей в строку состояния коннектора, я должен применить конструкцию  Return= Return or <Вызов модуля>
    Return=None
    factionkill.submit(cmdr, is_beta, system, station, entry,client)
    nhss.submit(cmdr, is_beta, system, station, entry,client)
    hdreport.submit(cmdr, is_beta, system, station, entry,client)
    codex.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    fssreports.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    journaldata.submit(cmdr, is_beta, system, station, entry,client)
    clientreport.submit(cmdr,is_beta,client,entry)
    this.patrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    this.codexcontrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    whiteList.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    materialReport.submit(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, x,y,z,body,lat,lon,client)
  


    #legacy to canonn
    Clegacy.statistics(cmdr, is_beta, system, station, entry, state)
    Clegacy.CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    Clegacy.AXZone(cmdr, is_beta, system,x,y,z, station, entry, state)
    Clegacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    Clegacy.NHSS.submit(cmdr, is_beta, system,x,y,z, station, entry,client)

    #Triumvirate reporting
    #FF.FriendFoe.friendFoe(cmdr, system, station, entry, state)

    bgs.EventRead(cmdr, is_beta, system, station, entry, client)

    legacy.shipscan(cmdr, is_beta, system, station, entry)
    Return= Return or modules.Commands.commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,this.fuel,this.fuel_cons,this.SRVmode,this.Fightermode)
    # legacy logging to google sheets
    legacy.statistics(cmdr, is_beta, system, station, entry, state)
    legacy.CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    legacy.AXZone(cmdr, is_beta, system,x,y,z, station, entry, state)
    legacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    legacy.NHSS.submit(cmdr, is_beta, system,x,y,z, station, entry,client)
    legacy.BGS().TaskCheck(cmdr, is_beta, system, station, entry, client)
    return Return
    
    
def fuel_consumption(entry,old_fuel,old_timestamp,old_fuel_cons):
    #debug(old_timestamp==entry["timestamp"])
    if  entry["timestamp"] !=old_timestamp and old_fuel!=0:
        try:
            fuel_cons=((old_fuel["FuelMain"]+old_fuel["FuelReservoir"])-(entry["Fuel"]["FuelMain"]+entry["Fuel"]["FuelReservoir"]))/float((datetime.strptime (entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")-old_timestamp).total_seconds())
        except ZeroDivisionError:
            return old_fuel_cons
        #debug("Fuel consumption is "+str(fuel_cons))
        return fuel_cons
    else:
        #debug("Can't calculate fuel consumption")
        return old_fuel_cons
    


this.FuelCount=9
this.plug_start=False
def dashboard_entry(cmdr, is_beta, entry):
    debug(entry)
    if this.plug_start==0:
        this.plug_start=1
        this.fuel=entry["Fuel"]
        this.old_time=datetime.strptime (entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    try:
        debug("Checking fuel consumption "+str(this.FuelCount))
        if this.FuelCount==10:
            this.fuel_cons=fuel_consumption(entry,this.fuel,this.old_time,this.fuel_cons)
            this.old_time=datetime.strptime (entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            this.fuel=entry["Fuel"]
            this.FuelCount=0
        else: this.FuelCount+=1
    except NameError :
        #debug("Can't check fuel consumption, waiting for data")
        this.fuel_cons = 0
    
    #debug("Dashboard update "+str(entry["Fuel"]))
    

    this.landed = entry['Flags'] & 1<<1 and True or False
    this.SCmode = entry['Flags'] & 1<<4 and True or False
    this.SRVmode = entry['Flags'] & 1<<26 and True or False
    this.Fightermode = entry['Flags'] & 1<<25 and True or False
    this.landed = this.landed or this.SRVmode
      #print 'LatLon = {}'.format(entry['Flags'] & 1<<21 and True or False)
      #print entry
    if(entry['Flags'] & 1<<21 and True or False):
        if('Latitude' in entry):
            this.nearloc['Latitude'] = entry['Latitude']
            this.nearloc['Longitude'] = entry['Longitude']
    else:
       
        this.nearloc['Latitude'] = None
        this.nearloc['Longitude'] = None
    if entry.get("BodyName"):
        this.body_name=entry.get("BodyName")
    else:
        this.body_name = None   
    debug(this.body_name)    
    this.cmdr_SQID=Alegiance_get(cmdr,this.cmdr_SQID)
    #debug(this.cmdr_SQID)
    
    
def cmdr_data(data, is_beta):
    '''
    We have new data on our commander
    '''
    #debug(json.dumps(data,indent=4))
    this.patrol.cmdr_data(data, is_beta)


def startup_stats(cmdr):
    try:
        this.first_event
    except:
      this.first_event = True
      addr = requests.get('https://api.ipify.org').text
      addr6 = requests.get('https://api6.ipify.org').text
      url="https://docs.google.com/forms/d/1h7LG5dEi07ymJCwp9Uqf_1phbRnhk1R3np7uBEllT-Y/formResponse?usp=pp_url"
      url+="&entry.1181808218="+quote_plus(cmdr)
      url+="&entry.254549730="+quote_plus(this.version)
      url+="&entry.1622540328="+quote_plus(addr)
      if addr6 != addr:
          url+="&entry.488844173="+quote_plus(addr6)
      else:
          url+="&entry.488844173="+quote_plus("0")
      url+="&entry.1210213202="+str(release.get_auto())
      
      legacy.Reporter(url).start()
