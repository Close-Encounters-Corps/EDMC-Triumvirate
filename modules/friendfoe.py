
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

        if self.CMDRRow2["text"]!=["PlaceHolder"]:
            self.CMDRRow2.grid()

        if self.CMDRRow3["text"]!=["PlaceHolder"]:
            self.CMDRRow3.grid()

        if self.CMDRRow4["text"]!=["PlaceHolder"]:
            self.CMDRRow4.grid()
       
    def analysis(self,cmdr, is_beta, system, entry, client):
        if entry["event"]=="ShipTargeted" and entry["TargetLocked"]==True and "$cmdr_decorate" in entry["PilotName"]:
            debug("Yay")
            tCmdr=entry["PilotName"].split("=")[1].replace(";","")
            debug(tCmdr)
        
    

    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):          
        "Called to get a tk Frame for the settings dialog."

        self.FFSwitch=tk.IntVar(value=config.getint('Triumvirate:'+"FFSwitch"))
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
     if cmdr and not is_beta:
        self.cmdr = cmdr
        
        cmdrs = config.get('inara_cmdrs') 
        apikeys = config.get('inara_apikeys') 
        if cmdr in cmdrs:
            idx = cmdrs.index(cmdr)
            apikeys.extend([''] * (1 + idx - len(apikeys)))
            changed |= (apikeys[idx] != this.apikey.get().strip())
            apikeys[idx] = this.apikey.get().strip()

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."     
        config.set('Triumvirate:'++"FFSwitch", self.FFSwitch.get())      
        config.set('Triumvirate:'++'ResponderSwitch', self.ResponderSwitch.get())      
        config.set('Triumvirate:'++'VisibilitySwitch', self.VisibilitySwitch.get())   
        config.set('Triumvirate:'++'InaraSwitch', self.InaraSwitch.get())



        
  
    @classmethod    
    def plugin_start(cls,plugin_dir):
        cls.plugin_dir=unicode(plugin_dir)