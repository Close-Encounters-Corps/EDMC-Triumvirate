
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
import importlib
import time



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
this = sys.modules [__name__]	# For holding module globals
this.queue = Queue ()



class ReleaseLink ( HyperlinkLabel ):

    def __init__ ( self, parent ):

        HyperlinkLabel.__init__ ( self,
            parent,
            text="PlaceHolder",
            url=None,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW )
        self.bind ( '<Configure>', self.__configure_event )

    def __configure_event ( self, event ):
        "Handle resizing."

        self.configure ( wraplength=event.width )

FFinstance = None

class FriendFoe ( Frame ):

    def __init__ ( self, parent,gridrow ):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__ ( self,
            parent )
        
        self.inaraKey = None
        self.CMDR = None 
        #получение переменных из
        #хранилища #TODO поменять
        #значения на нужные
        #для ФФ
        self.FFSwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "FFSwitch" ) )
        self.ResponderSwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "ResponderSwitch" ) )
        self.VisibilitySwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "VisibilitySwitch" ) )
        self.InaraSwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "InaraSwitch" ) )
        
        #Иницилизация контейнера для
        #интерфейса
        self.columnconfigure ( 1, weight=1 )                                       
        self.grid ( row = gridrow, column = 0, sticky="NSEW",columnspan=2 )
        
        self.label = tk.Label ( self, text=  "Свой чужой:" )
        self.label.grid ( row = 0, column = 0, sticky=sticky )
        self.label.grid_remove ()
        
        CurrentRow = 1
        Rows = 4#tk.IntVar(value=config.getint('Triumvirate:'+"FFRows"))
        self.RowsList = [i for i in range ( 1,Rows + 1 )]
        for index in self.RowsList:
            
            debug ( index )
            setattr ( self,"CMDRRow" + str ( index ),ReleaseLink ( self ) )
            getattr ( self,"CMDRRow" + str ( index ) ).grid ( row = index, column = 0, sticky=sticky )
            getattr ( self,"CMDRRow" + str ( index ) ).grid_remove ()
            #debug ( getattr ( self,"CMDRRow" + str ( index ) ) )


            setattr ( self,"SQIDRow" + str ( index ), ReleaseLink ( self ) )
            getattr ( self,"SQIDRow" + str ( index ) ).grid ( row = index, column = 1, sticky=sticky )
            getattr ( self,"SQIDRow" + str ( index ) ).grid_remove ()

            setattr ( self,"StateRow" + str ( index ),  tk.Label ( self, text=  "state" ) )
            getattr ( self,"StateRow" + str ( index ) ).grid ( row = index, column = 2, sticky=sticky )
            getattr ( self,"StateRow" + str ( index ) ).grid_remove ()

            CurrentRow = CurrentRow + 1

    @classmethod    
    def plugin_start ( cls,plugin_dir,version ):
        #plugin_dir_name=plugin_dir.split("\\")[-1]
        #debug(plugin_dir_name)
        #cls.load=importlib.import_module("..load",
        #plugin_dir_name)
        cls.version = version
        cls.plugin_dir = unicode ( plugin_dir )    

                

    
    def listOffset ( self,targetCmdr,targetUrl = None,targetSquadron = "N/A",targetSquadronUrl = None,state = "N/A" ):
        debug(str(targetCmdr)+str(targetUrl)+str(targetSquadron) +str(targetSquadronUrl) +str(state) )
        self.CMDRsInSight = []    
        for index in self.RowsList:
            self.CMDRsInSight.append ( getattr ( self,"CMDRRow" + str ( index ) ) ['text'] )
        if targetCmdr in self.CMDRsInSight:      #Если запись об пилоте уже есть
                                                 #на
                                                                                            #интерфейсе,
                                                                                            #обновить
                                                                                            #поля,
                                                                                            #если
                                                                                            #нет,
                                                                                            #то
                                                #добавить
                                                                                           #ее
                                                                                           #наверх
                                                                                           #списка
            debug("updating info for CMDR={} with data TURL={}, TSQID={}, SQIDURL={}, State={}".format(targetCmdr,targetUrl,targetSquadron,targetSquadronUrl,state))
            index = self.CMDRsInSight.index ( targetCmdr )
            if targetUrl !=None: getattr ( self,"CMDRRow" + str ( index + 1 ) ) ['url'] = targetUrl
            if targetSquadron !="N/A":getattr ( self,"SQIDRow" + str ( index + 1 ) ) ['text']  = targetSquadron
            if targetSquadronUrl !=None:getattr ( self,"SQIDRow" + str ( index + 1 ) ) ['url'] = targetSquadronUrl
            if state !="N/A":getattr ( self,"StateRow" + str ( index + 1 ) ) ['text'] = state
            return

        for index in reversed ( self.RowsList ):
            if index != 1:
                debug("moving data from {}".format(index))
                getattr ( self,"CMDRRow" + str ( index ) ) ['text'] = getattr ( self,"CMDRRow" + str ( index - 1 ) ) ['text']
                try:getattr ( self,"CMDRRow" + str ( index ) ) ['url'] = getattr ( self,"CMDRRow" + str ( index - 1 ) ) ['url'] 
                except: debug ( "nothing to move" )
                getattr ( self,"SQIDRow" + str ( index ) ) ['text'] = getattr ( self,"SQIDRow" + str ( index - 1 ) ) ['text']
                try:getattr ( self,"SQIDRow" + str ( index ) ) ['url'] = getattr ( self,"SQIDRow" + str ( index - 1 ) ) ['url']
                except: debug ( "nothing to move" )
                getattr ( self,"StateRow" + str ( index ) ) ['text'] = getattr ( self,"StateRow" + str ( index - 1 ) ) ['text']
            else:
                debug("Adding info to table: CMDR={}, TURL={}, TSQID={}, SQIDURL={}, State={}".format(targetCmdr,targetUrl,targetSquadron,targetSquadronUrl,state))
                getattr ( self,"CMDRRow" + str ( index ) ) ['text'] = targetCmdr
                getattr ( self,"CMDRRow" + str ( index ) ) ['url'] = targetUrl
                getattr ( self,"SQIDRow" + str ( index ) ) ['text'] = targetSquadron
                getattr ( self,"SQIDRow" + str ( index ) ) ['url'] = targetSquadronUrl
                getattr ( self,"StateRow" + str ( index ) ) ['text'] = state

        self.label.grid ()
        for index in  ( self.RowsList ):
            if getattr ( self,"CMDRRow" + str ( index ) ) ['text'] != "PlaceHolder":
                debug("Showing up data from row "+index)
                getattr ( self,"CMDRRow" + str ( index ) ).grid () 
                getattr ( self,"SQIDRow" + str ( index ) ).grid ()
                getattr ( self,"StateRow" + str ( index ) ).grid ()
                return

        
            
    DetectedCommanders = {}            
    def analysis ( self,cmdr, is_beta, system, entry, client ):
        if self.FFSwitch==1:
            if entry ["event"] == "ShipTargeted" and entry ["TargetLocked"] == True and entry ["ScanStage"] >= 1 and "$cmdr_decorate:#name=" in entry ["PilotName"]:
                debug ( "Yay" )
                tCMDRData = [ None,None,None,None ] #DetectedCommanders={cmdr1:[tUrl,tSQID,tSQIDUrl,state],}
            
                tCmdr = entry ["PilotName"].split ( "=" ) [1].replace ( ";","" )
                if tCmdr in self.DetectedCommanders:
                    tCMDRData = self.DetectedCommanders [tCmdr]
                    tCMDRData [1] = entry.get ( "SquadronID","N/A" )
                elif entry ["ScanStage"] == 3:
                    tCMDRData [1] = entry.get ( "SquadronID","N/A" )
                elif tCmdr not in self.DetectedCommanders:
                    InaraConnect ( eventName="getCommanderProfile",eventData={"searchName":tCmdr},callback=self.InaraParse ).start ()
                self.listOffset ( tCmdr,tCMDRData [0],tCMDRData [1],tCMDRData [2],tCMDRData [3] )
                self.DetectedCommanders [tCmdr] = tCMDRData
                self.connectToFFBase ( tCmdr )
                debug ( tCmdr )
        
    def connectToFFBase (self, tCmdr ):
        pass

    def InaraParse ( self,entry ):
        debug ( "Starting analysys of Inara Response" )
        entry = entry ["events"]
        
        for i in entry:
            if i ["eventStatus"]==200:
                debug ( i )
                tCMDR = i ["eventData"] ["userName"]
                tCMDRUrl = i ["eventData"] ["inaraURL"]
                tSQID = i ["eventData"] ["commanderWing"] ["wingName"]
                tSQIDUrl = i ["eventData"] ["commanderWing"] ["inaraURL"]
                self.DetectedCommanders [tCMDR] [0] = tCMDRUrl
                self.DetectedCommanders [tCMDR] [2] = tSQIDUrl
                self.listOffset ( tCMDR,tCMDRUrl,tSQID,tSQIDUrl )


    def plugin_prefs ( self, parent, cmdr, is_beta,gridrow ):          
        "Called to get a tk Frame for the settings dialog."

        self.FFSwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:FFSwitch' ) )    #TODO прорефакторить вызов настроек
        self.ResponderSwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "ResponderSwitch" ) )
        self.VisibilitySwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "VisibilitySwitch" ) )
        self.InaraSwitch = tk.IntVar ( value=config.getint ( 'Triumvirate:' + "InaraSwitch" ) )
        
        frame = nb.Frame ( parent )
        frame.columnconfigure ( 2, weight=1 )
        frame.grid ( row = gridrow, column = 0,sticky="NSEW" )
        nb.Label ( frame,text=       "Система опознавания «свой-чужой»" ).grid ( row=0,column=0,sticky="NW" )
        nb.Checkbutton ( frame, text="Включить модуль «свой-чужой»", variable=self.FFSwitch ).grid ( row = 1, column = 0,sticky="NW" )
        nb.Checkbutton ( frame, text="Сообщать о нападении", variable=self.ResponderSwitch ).grid ( row = 1, column = 1,sticky="NW" )
        nb.Checkbutton ( frame, text="Показать в интерфейсе", variable=self.VisibilitySwitch ).grid ( row = 2, column = 1,sticky="NW" )
        nb.Checkbutton ( frame, text="Подключится к Инаре\n(требуется установленный\nключ API на вкладке Inara)", variable=self.InaraSwitch ).grid ( row = 2, column = 0,sticky="NW" )
                                    
        return frame



    @classmethod
    def Inara_Prefs ( cls,cmdr = None ):
     #if cmdr is None:
         #try: cmdr=CMDR
         #except: debug("Ebaniy Rot
         #Etogo Casino")
     if config.getint ( 'Triumvirate:' + "InaraSwitch" ) == 1 and cmdr :
        cls.CMDR = cmdr
        
        if not cmdr:
            return None

        cmdrs = config.get ( 'inara_cmdrs' ) or []
        if cmdr in cmdrs and config.get ( 'inara_apikeys' ):
            cls.inaraKey = config.get ( 'inara_apikeys' ) [cmdrs.index ( cmdr )]
        


    def CMDR_Fetch ( self,cmdr ):
        self.CMDR = cmdr
        self.Inara_Prefs ( cmdr )


    def prefs_changed ( self, cmdr, is_beta ):
        "Called when the user clicks OK on the settings dialog."     
        config.set ( 'Triumvirate:FFSwitch', self.FFSwitch.get () )      
        config.set ( 'Triumvirate:ResponderSwitch', self.ResponderSwitch.get () )      
        config.set ( 'Triumvirate:VisibilitySwitch', self.VisibilitySwitch.get () )   
        config.set ( 'Triumvirate:InaraSwitch', self.InaraSwitch.get () )
        self.Inara_Prefs ( cmdr )



        
  






class InaraConnect ( threading.Thread ):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    url = "https://inara.cz/inapi/v1/"
        
        
        
    def __init__ ( self,eventName = None,eventData = None,EventsJSON = None,callback = None ):
        threading.Thread.__init__ ( self )
        
        if FriendFoe.inaraKey is not None:
            self.payload ["header"] ["APIkey"] = FriendFoe.inaraKey 
        else:Inara_Prefs ( cmdr ) 
        self.payload = {"header":{},"events":[]}
        self.payload ["header"] ["appName"] = "Triumvirate"  
        self.payload ["header"] ["appVersion"] = FriendFoe.version

        self.payload ["header"] ["commanderName"] = FriendFoe.CMDR 
        #self.payload["header"]["commanderFrontierID"]=this.load.CMDR
        if eventName is not None:
            EventsJSON = {"eventName":eventName,"eventTimestamp":time.strftime ( "%Y-%m-%dT%H:%M:%SZ" ,time.gmtime () ),"eventData":eventData}
            #self.payload["events"][0]["eventName"]=eventName
            #self.payload["events"][0]["eventTimestamp"]=time.strftime("%Y-%m-%dT%H:%M:%SZ"
            #,time.gmtime())
            #self.payload["events"][0]["eventData"]=eventData
            self.payload ["events"].append ( EventsJSON )
        elif EventsJSON is not None:
            self.payload ["events"].append ( EventsJSON )

        #self.returner=returner
        self.callback = callback


    @classmethod
    def setRoute ( cls ):
        # first check to see if we are
        # an official release
        
        client = FriendFoe.version
        r = requests.get ( "https://api.github.com/repos/VAKazakov/EDMC-Triumvirate/releases/tags/{}".format ( client ) )
        j = r.json ()
        if r.status_code == 404:
            debug ( "Release not in github" )
            isDeveloped = True
        elif j.get ( "prerelease" ):
            debug ( "Prerelease in github" )
            isDeveloped = True
        else:
            debug ( "Release in github" )
            isDeveloped = False

        return isDeveloped
            

                
        

        

           
    
    def run ( self ):
    
        #configure the payload
        
        self.payload ["header"] ["isDeveloped"] = self.setRoute ()
        debug ( "starting connetion to inara" )
        self.send ( self.payload,self.url )
    
    def send ( self,payload,url ):
        debug ( "atempring pust to inara " + str ( payload ) )
        r = requests.post ( url,data=json.dumps ( payload, ensure_ascii=False ).encode ( 'utf-8' ),headers={"content-type":"application/json"} )  
        
        if not r.status_code == requests.codes.ok:
            
            error ( r.status_code )
            error ( r.json () )
            error ( json.dumps ( payload ) )
        elif self.callback is not None:
            debug ( json.dumps ( r.json (),indent=4 ) )
            self.callback ( r.json () )
            #self.callback is not None:
            #self.callback(r)
            


# Worker thread
def worker ():
    while True:
        item = queue.get ()
        if not item:
            return	# Closing
        else:
            ( url, data, callback ) = item

        retrying = 0
        while retrying < 3:
            try:
                r = this.session.post ( url, data=json.dumps ( data, separators = ( ',', ':' ) ), timeout=_TIMEOUT )
                r.raise_for_status ()
                reply = r.json ()
                status = reply ['header'] ['eventStatus']
                if callback:
                    callback ( reply )
                elif status // 100 != 2:	# 2xx == OK (maybe with warnings)
                    # Log fatal errors
                    print 'Inara\t%s %s' % ( reply ['header'] ['eventStatus'], reply ['header'].get ( 'eventStatusText', '' ) )
                    print json.dumps ( data, indent = 2, separators = ( ',', ': ' ) )
                    plug.show_error ( _ ( 'Error: Inara {MSG}' ).format ( MSG = reply ['header'].get ( 'eventStatusText', status ) ) )
                else:
                    # Log individual
                    # errors and
                    # warnings
                    for data_event, reply_event in zip ( data ['events'], reply ['events'] ):
                        if reply_event ['eventStatus'] != 200:
                            print 'Inara\t%s %s\t%s' % ( reply_event ['eventStatus'], reply_event.get ( 'eventStatusText', '' ), json.dumps ( data_event ) )
                            if reply_event ['eventStatus'] // 100 != 2:
                                plug.show_error ( _ ( 'Error: Inara {MSG}' ).format ( MSG = '%s, %s' % ( data_event ['eventName'], reply_event.get ( 'eventStatusText', reply_event ['eventStatus'] ) ) ) )
 

                break
            except:
                if __debug__: print_exc ()
                retrying += 1
        else:
            if callback:
                callback ( None )
            else:
                plug.show_error ( _ ( "Error: Can't connect to Inara" ) )