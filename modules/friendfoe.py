
#coding=utf-8
'''
    Модуль, осуществляющий поиск сквадронов и пилотов в базах данных ЕГУ, а в случае не обнаружения отправляющий новые данные 
'''
import Tkinter as tk
from Tkinter import Frame
import uuid
from ttkHyperlinkLabel import HyperlinkLabel
import requests
import json
import re
import myNotebook as nb
from config import config
import threading
from debug import Debug
from debug import debug,error
from Queue import Queue
import sys



'''
{ "timestamp":"2019-04-29T19:27:30Z", 
"event":"ShipTargeted", 
"TargetLocked":true, 
"Ship":"krait_mkii", 
"Ship_Localised":"Krait Mk II", 
"ScanStage":3, 
"PilotName":"$cmdr_decorate:#name=GromoZekka;", 
"PilotName_Localised":"КМДР GromoZekka", 
"PilotRank":"Elite", 
"SquadronID":"EGPU", 
"ShieldHealth":78.094543, 
"HullHealth":36.569859, 
"LegalStatus":"Clean" }

{ "timestamp":"2019-04-28T20:48:48Z", 
"event":"ShipTargeted", 
"TargetLocked":true, 
"Ship":"orca", 
"ScanStage":3, 
"PilotName":"$npc_name_decorate:#name=Pit Thomsen;",
"PilotName_Localised":"Pit Thomsen", 
"PilotRank":"Dangerous", 
"ShieldHealth":100.000000, 
"HullHealth":100.000000, 
"Faction":"Clayakarma Electronics Limited", 
"LegalStatus":"Clean" }

Заметка №1 отсеивать игроков следует через конструкцию if "$cmdr_decorate" in entry["PilotName"] 
Заметка №1.2 стоит посмотреть, как определяются нпс пилоты истребителей  (неактуально)
Заметка №2 скорее всего, проще всего определять имя пилота по той же строке, что и неписей (неактуально)
Заметка №2.1 имеет смысл убирать #name= через строчные функции (TargetName=entry["PilotName"].split("=")[1])
Заметка №3 модуль не должно быть видно, пока нет данных. так же как это реализовано в release.py
'''
this = sys.modules[__name__]	# For holding module globals
this.queue = Queue()


class ReleaseLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="PlaceHolder",
            url="",
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.bind('<Configure>', self.__configure_event)

    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)

class FriendFoe(Frame):

    def __init__(self, parent,gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
        
        self.inaraKey=None
        #получение переменных из хранилища #TODO поменять значения на нужные для ФФ
        self.FFSwitch=tk.IntVar(value=config.getint('Triumvirate:'+"FFSwitch"))
        self.ResponderSwitch=tk.IntVar(value=config.getint('Triumvirate:'+"ResponderSwitch"))
        self.VisibilitySwitch=tk.IntVar(value=config.getint('Triumvirate:'+"VisibilitySwitch"))
        
        
        #Иницилизация контейнера для интерфейса
        self.columnconfigure(1, weight=1)                                       
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        
        self.label=tk.Label(self, text=  "Свой чужой:")
        self.label.grid(row = 0, column = 0, sticky=sticky)
        self.label.grid_remove()
        
        self.CMDRRow1=ReleaseLink(self)
        self.CMDRRow1.grid(row = 1, column = 0, sticky=sticky)
        self.CMDRRow1.grid_remove()

        self.SQIDRow1=ReleaseLink(self)
        self.SQIDRow1.grid(row = 1, column = 1,sticky="NSEW")
        self.SQIDRow1.grid_remove()

        self.StateRow1 =tk.Label(self, text=  "state")
        self.StateRow1.grid(row = 1, column = 2, sticky=sticky)
        self.StateRow1.grid_remove()


        self.CMDRRow2=ReleaseLink(self)
        self.CMDRRow2.grid(row = 2, column = 0, sticky=sticky)
        self.CMDRRow2.grid_remove()
        
        self.SQIDRow2=ReleaseLink(self)
        self.SQIDRow2.grid(row = 2, column = 1,sticky="NSEW")
        self.SQIDRow2.grid_remove()

        self.StateRow2 =tk.Label(self, text=  "state")
        self.StateRow2.grid(row = 2, column = 2, sticky=sticky)
        self.StateRow2.grid_remove()

        self.CMDRRow3=ReleaseLink(self)
        self.CMDRRow3.grid(row = 3, column = 0, sticky=sticky)
        self.CMDRRow3.grid_remove()
        
        self.SQIDRow3=ReleaseLink(self)
        self.SQIDRow3.grid(row = 3, column = 1,sticky="NSEW")
        self.SQIDRow3.grid_remove()

        self.StateRow3 =tk.Label(self, text=  "state")
        self.StateRow3.grid(row = 3, column = 2, sticky=sticky)
        self.StateRow3.grid_remove()
        
        self.CMDRRow4=ReleaseLink(self)
        self.CMDRRow4.grid(row = 4, column = 0, sticky=sticky)
        self.CMDRRow4.grid_remove()
        
        self.SQIDRow4=ReleaseLink(self)
        self.SQIDRow4.grid(row = 4, column = 1,sticky="NSEW")
        self.SQIDRow4.grid_remove()

        self.StateRow4 =tk.Label(self, text=  "state")
        self.StateRow4.grid(row = 4, column = 2, sticky=sticky)
        self.StateRow4.grid_remove()

                

            
    def listOffset(self,targetCmdr,targetSquadron,targetUrl,targetSquadronUrl,state):
        self.CMDRRow4["text"],self.CMDRRow4['url'],self.SQIDRow4["text"],self.SQIDRow4["url"],self.StateRow4["text"]= self.CMDRRow3["text"],self.CMDRRow3['url'],self.SQIDRow3["text"],self.SQIDRow3["url"],self.StateRow3["text"]
        self.CMDRRow3["text"],self.CMDRRow3['url'],self.SQIDRow3["text"],self.SQIDRow3["url"],self.StateRow3["text"]= self.CMDRRow2["text"],self.CMDRRow2['url'],self.SQIDRow2["text"],self.SQIDRow2["url"],self.StateRow2["text"]
        self.CMDRRow2["text"],self.CMDRRow2['url'],self.SQIDRow2["text"],self.SQIDRow2["url"],self.StateRow2["text"]= self.CMDRRow1["text"],self.CMDRRow1['url'],self.SQIDRow1["text"],self.SQIDRow1["url"],self.StateRow1["text"]
        self.CMDRRow1["text"],self.CMDRRow1['url'],self.SQIDRow1["text"],self.SQIDRow1["url"],self.StateRow1["text"]= targetCmdr,targetSquadron,targetUrl,targetSquadronUrl,state

        if self.CMDRRow1["text"]!=["PlaceHolder"]:
            self.label.grid()
            self.CMDRRow1.grid()
            self.SQIDRow1.grid()
            self.StateRow1.grid()

        if self.CMDRRow2["text"]!=["PlaceHolder"]:
            self.CMDRRow2.grid()
            self.SQIDRow2.grid()
            self.StateRow2.grid()

        if self.CMDRRow3["text"]!=["PlaceHolder"]:
            self.CMDRRow3.grid()
            self.SQIDRow3.grid()
            self.StateRow3.grid()

        if self.CMDRRow4["text"]!=["PlaceHolder"]:
            self.CMDRRow4.grid()
            self.SQIDRow4.grid()
            self.StateRow4.grid()
            
            
    def analysis(self,cmdr, is_beta, system, entry, client):
        if entry["event"]=="ShipTargeted" and entry["TargetLocked"]==True and entry["ScanStage"]>=1 and "$cmdr_decorate" in entry["PilotName"]:
            debug("Yay")
            tCmdr=entry["PilotName"].split("=")[1].replace(";","")
            debug(tCmdr)
        
    

    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):          
        "Called to get a tk Frame for the settings dialog."

        self.FFSwitch=tk.IntVar(value=config.getint('Triumvirate:FFSwitch'))    #TODO прорефакторить вызов настроек
        self.ResponderSwitch=tk.IntVar(value=config.getint('Triumvirate:'+"ResponderSwitch"))
        self.VisibilitySwitch=tk.IntVar(value=config.getint('Triumvirate:'+"VisibilitySwitch"))
        self.InaraSwitch=tk.IntVar(value=config.getint('Triumvirate:'+"InaraSwitch"))
        
        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        frame.grid(row = gridrow, column = 0,sticky="NSEW")
        nb.Label(frame,text=       "Система опознавания «свой-чужой»").grid(row=0,column=0,sticky="NW")
        nb.Checkbutton(frame, text="Включить модуль «свой-чужой»", variable=self.FFSwitch).grid(row = 1, column = 0,sticky="NW")
        nb.Checkbutton(frame, text="Сообщать о нападении", variable=self.ResponderSwitch).grid(row = 1, column = 1,sticky="NW")
        nb.Checkbutton(frame, text="Показать в интерфейсе", variable=self.VisibilitySwitch).grid(row = 2, column = 1,sticky="NW")
        nb.Checkbutton(frame, text="Подключится к Инаре\n(требуется установленный\nключ API на вкладке Inara)", variable=self.InaraSwitch).grid(row = 2, column = 0,sticky="NW")
                                    
        return frame




    def Inara_Prefs(self,cmdr,is_beta):
     if self.InaraSwitch==1 and cmdr and not is_beta:
        self.cmdr = cmdr
        
        cmdrs = config.get('inara_cmdrs') 
        apikeys = config.get('inara_apikeys') 
        if cmdr in cmdrs:
            idx = cmdrs.index(cmdr)
            self.inaraKey=apikeys[idx]





    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."     
        config.set('Triumvirate:FFSwitch", self.FFSwitch.get())      
        config.set('Triumvirate:ResponderSwitch', self.ResponderSwitch.get())      
        config.set('Triumvirate:VisibilitySwitch', self.VisibilitySwitch.get())   
        config.set('Triumvirate:InaraSwitch', self.InaraSwitch.get())



        
  
    @classmethod    
    def plugin_start(cls,plugin_dir):
        cls.thread = threading.Thread(target = worker, name = 'Inara worker')
        cls.thread.daemon = True
        cls.thread.start()
        cls.plugin_dir=unicode(plugin_dir)





class InaraConnect(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    url="https://inara.cz/inapi/v1/"
        
        
        
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        threading.Thread.__init__(self)
        self.cmdr=cmdr
        self.system=system
        self.x=x
        self.y=y
        self.z=z
        self.body = body
        self.lat = lat
        self.lon = lon
        self.is_beta = is_beta
        if entry:
            self.entry = entry.copy()
        self.client = client
        Emitter.setRoute(is_beta,client)
        self.modelreport="clientreports"

    @classmethod
    def setRoute(cls,is_beta,client):
        if Emitter.route:
            return Emitter.route
        else:
            # first check to see if we are an official release
            repo,tag=client.split(".",1)
            r=requests.get("https://api.github.com/repos/VAKazakov/{}/releases/tags/{}".format(repo,tag))
            j=r.json()
            if r.status_code == 404:
                debug("Release not in github")
                Emitter.route=Emitter.urls.get("development")
            elif j.get("prerelease"):
                debug("Prerelease in github")
                Emitter.route=Emitter.urls.get("staging")
            else:
                debug("Release in github")
                Emitter.route=Emitter.urls.get("live")
            

                
        return Emitter.route

        
    def getUrl(self):
        if self.is_beta:
            url=Emitter.urls.get("staging")
        else:
            url=Emitter.route
        return url
        
    def setPayload(self):
        payload={}
        payload["cmdrName"]=self.cmdr  
        payload["systemName"]=self.system
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
        return payload   
    
    def run(self):
    
        #configure the payload       
        payload=self.setPayload()
        url=self.getUrl()
        self.send(payload,url)
    
    def send(self,payload,url):
        fullurl="{}/{}".format(url,self.modelreport)
        r=requests.post(fullurl,data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),headers={"content-type":"application/json"})  
        
        if not r.status_code == requests.codes.ok:
            error("{}/{}".format(url,self.modelreport))
            error(r.status_code)
            error(r.json())
            error(json.dumps(payload))
        else:
            debug("{}?id={}".format(fullurl,r.json().get("id")))


# Worker thread
def worker():
    while True:
        item = queue.get()
        if not item:
            return	# Closing
        else:
            (url, data, callback) = item

        retrying = 0
        while retrying < 3:
            try:
                r = this.session.post(url, data=json.dumps(data, separators = (',', ':')), timeout=_TIMEOUT)
                r.raise_for_status()
                reply = r.json()
                status = reply['header']['eventStatus']
                if callback:
                    callback(reply)
                elif status // 100 != 2:	# 2xx == OK (maybe with warnings)
                    # Log fatal errors
                    print 'Inara\t%s %s' % (reply['header']['eventStatus'], reply['header'].get('eventStatusText', ''))
                    print json.dumps(data, indent=2, separators = (',', ': '))
                    plug.show_error(_('Error: Inara {MSG}').format(MSG = reply['header'].get('eventStatusText', status)))
                else:
                    # Log individual errors and warnings
                    for data_event, reply_event in zip(data['events'], reply['events']):
                        if reply_event['eventStatus'] != 200:
                            print 'Inara\t%s %s\t%s' % (reply_event['eventStatus'], reply_event.get('eventStatusText', ''), json.dumps(data_event))
                            if reply_event['eventStatus'] // 100 != 2:
                                plug.show_error(_('Error: Inara {MSG}').format(MSG = '%s, %s' % (data_event['eventName'], reply_event.get('eventStatusText', reply_event['eventStatus']))))
                        if data_event['eventName'] in ['addCommanderTravelDock', 'addCommanderTravelFSDJump', 'setCommanderTravelLocation']:
                            eventData = reply_event.get('eventData', {})
                            this.system  = eventData.get('starsystemInaraURL')
                            if config.get('system_provider') == 'Inara':
                                this.system_link['url'] = this.system	# Override standard URL function
                            this.station = eventData.get('stationInaraURL')
                            if config.get('station_provider') == 'Inara':
                                this.station_link['url'] = this.station or this.system	# Override standard URL function
                break
            except:
                if __debug__: print_exc()
                retrying += 1
        else:
            if callback:
                callback(None)
            else:
                plug.show_error(_("Error: Can't connect to Inara"))