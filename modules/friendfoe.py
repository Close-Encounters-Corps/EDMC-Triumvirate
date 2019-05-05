
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
'''




class FriendFoe(Frame):
    def __init__(self, parent,gridrow):
        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
        self.hidden=tk.IntVar(value=config.getint('HideFF'))


    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        'Called to get a tk Frame for the settings dialog.'
    
        this.self.hidden=tk.IntVar(value=config.getint('HideFF'))
        
        #frame = nb.Frame(parent)
        #frame.columnconfigure(1, weight=1)
        return nb.Checkbutton(parent, text='Hide Friend/Foe system', variable=self.hidden).grid(row = gridrow, column = 0,sticky='NSEW')
        
        #return frame

    def visible(self):
        if self.hidden.get() == 1:
            self.grid_remove()
            self.isvisible=False
            return False
        else:
            self.grid()
            self.isvisible=True
            return True

    def prefs_changed(self, cmdr, is_beta):
        'Called when the user clicks OK on the settings dialog.'
        config.set('HideFF', self.hidden.get())      
        if self.visible():
            self.news_update()
    
    def isCMDR(input):
        types={
            '$cmdr_decorate':'cmdr',
            '$npc_name_decorate':'npc'}
        type=input.split(':')
        output=types[type[0]]
        return output


    def friendFoe(cmdr, system, station, entry, state):
        if entry['event']=='ShipTargeted':
            if isCMDR(entry['PilotName'])=='cmdr':
                tCMDR=entry['PilotName'].split(':')
                tCMDR=tCMDR[1]
                debug("in sight cmdr "+tCMDR)            