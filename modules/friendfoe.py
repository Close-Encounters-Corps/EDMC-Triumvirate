
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

Заметка №1 отсеивать неписей стоит по конструкции "PilotName":"$npc_name_decorate:#name=Pit Thomsen;", где параметром, прямо указывающим на НПСишность является $npc_name_decorate
Заметка №1.2 стоит посмотреть, как определяются нпс пилоты истребителей
Заметка №2 скорее всего, проще всего определять имя пилота по той же строке, что и неписей
Заметка №2.1 имеет смысл убирать #name= через строчные функции
Заметка №3 модуль не должно быть видно, пока нет данных. так же как это реализовано в release.py
'''

class ReleaseLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching...",
            url=DEFAULT_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.bind('<Configure>', self.__configure_event)

    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)

class FriendFoe(Frame):

    def __init__(self, parent,release,gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
        
        
        #получение переменных из хранилища #TODO поменять значения на нужные для ФФ
        self.auto=tk.IntVar(value=config.getint("AutoUpdate"))                    
        self.novoices=tk.IntVar(value=config.getint("NoVoices"))                
        self.rmbackup=tk.IntVar(value=config.getint("RemoveBackup"))                
        
        #Иницилизация контейнера для интерфейса
        self.columnconfigure(1, weight=1)                                       
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        
        self.label=tk.Label(self, text=  "Версия:")
        self.label.grid(row = 0, column = 0, sticky=sticky)
        
        
        self.hyperlink=ReleaseLink(self)
        self.hyperlink.grid(row = 0, column = 1,sticky="NSEW")
        
        self.button=tk.Button(self, text="Нажмите чтобы обновить", command=self.click_installer)
        self.button.grid(row = 1, column = 0,columnspan=2,sticky="NSEW")
        self.button.grid_remove()
        
        self.release=release
        self.news_count=0
        self.news_pos=0
        self.minutes=0
        self.latest={}
        self.update()
        #self.hyperlink.bind('<Configure>', self.hyperlink.configure_event)
        
        debug(config.get('Canonn:RemoveBackup'))
        
        if self.rmbackup.get() == 1  and config.get('Canonn:RemoveBackup') != "None":
            delete_dir=config.get('Canonn:RemoveBackup')
            debug('Canonn:RemoveBackup {}'.format(delete_dir))
            try:
                shutil.rmtree(delete_dir)
                
            except:
                error("Cant delete {}".format(delete_dir))
                
            ## lets not keep trying
            config.set('Canonn:RemoveBackup',"None")
            
        
        
       
        
        
    
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):          #TODO поменять на нужные для ФФ значения 
        "Called to get a tk Frame for the settings dialog."

        self.auto=tk.IntVar(value=config.getint("AutoUpdate"))
        self.rmbackup=tk.IntVar(value=config.getint("RemoveBackup"))
        self.novoices=tk.IntVar(value=config.getint("NoVoices"))
        
        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        frame.grid(row = gridrow, column = 0,sticky="NSEW")
        nb.Checkbutton(frame, text="Включить автообновление", variable=self.auto).grid(row = 0, column = 0,sticky="NW")
        nb.Checkbutton(frame, text="Удалять бекапы версий", variable=self.rmbackup).grid(row = 0, column = 1,sticky="NW")
        nb.Checkbutton(frame, text="Отключить голосовые сообщения", variable=self.novoices).grid(row = 0, column = 2,sticky="NW")
        
        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."    #TODO поменять на нужные для ФФ значения 
        config.set('AutoUpdate', self.auto.get())      
        config.set('RemoveBackup', self.rmbackup.get())      
        config.set('NoVoices', self.novoices.get())   
        



        
  
    @classmethod    
    def plugin_start(cls,plugin_dir):
        cls.plugin_dir=unicode(plugin_dir)