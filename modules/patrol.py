﻿# -*- coding: utf-8 -*-
"""
Patrols
"""

try: #py3
    import tkinter as tk
    from tkinter import Frame
    from urllib.parse import quote_plus
except: #py2
    import Tkinter as tk
    from Tkinter import Frame
    from urllib import quote_plus
import uuid
from ttkHyperlinkLabel import HyperlinkLabel
import requests
import json
import re
import myNotebook as nb
from config import config
import threading
from .systems import Systems
import math
from .debug import Debug
from .debug import debug, error
import csv
import os
from contextlib import closing
from datetime import datetime
from .release import Release
from l10n import Locale
import time
from . import legacy
from .lib.thread import Thread

CYCLE = 60 * 1000 * 60 # 60 minutes

DEFAULT_URL = ""
WRAP_LENGTH = 200

ship_types = {
        'adder': ' Adder',
        'typex_3': ' Alliance Challenger',
        'typex': ' Alliance Chieftain',
        'typex_2': ' Alliance Crusader',
        'anaconda': 'а Anaconda',
        'asp explorer': ' Asp Explorer',
        'asp': ' Asp Explorer',
        'asp scout': ' Asp Scout',
        'asp_scout': ' Asp Scout',
        'beluga liner': 'а Beluga Liner',
        'belugaliner': 'а Beluga Liner',
        'cobra mk. iii': 'а Cobra MkIII',
        'cobramkiii':  'а Cobra MkIII',
        'cobra mk. iv': 'а Cobra MkIV',
        'cobramkiv': 'а Cobra MkIV',
        'diamondback explorer': ' Diamondback Explorer',
        'diamondbackxl': ' Diamondback Explorer',
        'diamondback scout': ' Diamondback Scout',
        'diamondback': ' Diamondback Scout',
        'dolphin': ' Dolphin',
        'eagle': ' Eagle',
        'federal assault ship': ' Federal Assault Ship',
        'federation_dropship_mkii': ' Federal Assault Ship',
        'federal corvette': ' Federal Corvette',
        'federation_corvette': ' Federal Corvette',
        'federal dropship': ' Federal Dropship',
        'federation_dropship': ' Federal Dropship',
        'federal gunship': ' Federal Gunship',
        'federation_gunship': ' Federal Gunship',
        'fer-de-lance': ' Fer-de-Lance',
        'ferdelance': ' Fer-de-Lance',
        'hauler': ' Hauler',
        'imperial clipper': ' Imperial Clipper',
        'empire_trader': ' Imperial Clipper',
        'imperial courier': ' Imperial Courier',
        'empire_courier': ' Imperial Courier',
        'imperial cutter': ' Imperial Cutter',
        'cutter': ' Imperial Cutter',
        'imperial eagle': ' Imperial Eagle',
        'empire_eagle': ' Imperial Eagle',
        'keelback': ' Keelback',
        'independant_trader': ' Keelback',
        'krait_mkii': ' Krait MkII',
        'krait_light': ' Krait Phantom',
        'mamba': 'а Mamba',
        'orca': 'а Orca',
        'python': ' Python',
        'sidewinder': ' Sidewinder',
        'type 6 transporter': ' Type-6 Transporter',
        'type6': ' Type-6 Transporter',
        'type 7 transporter': ' Type-7 Transporter',
        'type7':' Type-7 Transporter',
        'type 9 heavy': ' Type-9 Heavy',
        'type9': ' Type-9 Heavy',
        'type 10 defender': ' Type-10 Defender',
        'type9_military': ' Type-10 Defender',
        'viper mk. iii': ' Viper MkIII',
        'viper': ' Viper MkIII',
        'viper mk. iv': ' Viper MkIV',
        'viper_mkiv': ' Viper MkIV',
        'vulture': 'а Vulture'
}
state_list = { #TODO Добавить локализацию новых состояний
    "civilliberty":"Гражданские свободы",
    "none":"",
    "boom":"Бум",
    "bust" : "Спад",
    "civilunrest":"Гражданские беспорядки",
    "civilwar":"Гражданская война",
    "election":"Выборы",
    "expansion":"Экспансия",
    "famine":"Голод",
    "investment":"Инвестиции",
    "lockdown":"Изоляция",
    "outbreak":"Эпдемия",
    "retreat":"Отступление",
    "war":"Война"}

def getShipType(key):
    try:
        name = ship_types.get(key.lower())
    except:
        return "NONE"
    if name:
        return name
    else:
        return key

def _callback(matches):
    id = matches.group(1)
    try:
        return chr(int(id))
    except:
        return id

class UpdateThread(Thread):
    def __init__(self, widget):
        Thread.__init__(self)
        self.widget = widget

    def run(self):
        debug("Patrol: UpdateThread")
        # download cannot contain any
        # tkinter changes
        self.widget.download()



def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)


def get(list,index):
    try:
        return list[index]
    except:
        return None

class PatrolLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(self,
            parent,
            text="Получение патруля",
            url=DEFAULT_URL,
            popup_copy = True,
            #wraplength=50, # updated
            #in __configure_event below
            anchor=tk.NW)
        #self.bind('<Configure>',
        #self.__configure_event)

    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)

class InfoLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(self,
            parent,
            text="Получение патруля",
            url=DEFAULT_URL,
            popup_copy = True,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW)
        self.resized = False
        self.bind('<Configure>', self.__configure_event)

    def __reset(self):
        self.resized = False

    def __configure_event(self, event):
        "Handle resizing."

        if not self.resized:
            self.resized = True
            self.configure(wraplength=event.width)
            self.after(500,self.__reset)

class CanonnPatrol(Frame):

    def __init__(self, parent,gridrow):
        "Initialise the ``Patrol``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        Frame.__init__(
            self,
            parent
            )
        self.ships = []
        self.bind('<<PatrolDone>>', self.update_ui)
        self.IMG_PREV = tk.PhotoImage(file = os.path.join(CanonnPatrol.plugin_dir,"icons","left_arrow.gif"))
        self.IMG_NEXT = tk.PhotoImage(file = os.path.join(CanonnPatrol.plugin_dir,"icons","right_arrow.gif"))

        self.patrol_config = os.path.join(Release.plugin_dir,'data','EDMC-Triumvirate.patrol')


        self.canonnbtn = tk.IntVar(value=config.getint("HidePatrol"))
        self.factionbtn = tk.IntVar(value=config.getint("Hidefactions"))
        self.hideshipsbtn = tk.IntVar(value=config.getint("HideMyShips"))
        self.edsmbtn = tk.IntVar(value=config.getint("HideEDSM"))
        self.copypatrolbtn = tk.IntVar(value=config.getint("CopyPatrolAdr"))


        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.HideMyShips = self.hideshipsbtn.get()
        self.CopyPatrolAdr = self.copypatrolbtn.get()
        self.edsm = self.edsmbtn.get()

        self.columnconfigure(1, weight=1)
        self.columnconfigure(4, weight=4)
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)

        ## Text Instructions for the
        ## patrol
        self.label = tk.Label(self, text=  "Патруль:")
        self.label.grid(row = 0, column = 0, sticky=sticky)

        self.hyperlink = PatrolLink(self)
        self.hyperlink.grid(row = 0, column = 2)
        self.distance = tk.Label(self, text=  "...")
        self.distance.grid(row = 0, column = 3,sticky="NSEW")
        self.distance.grid_remove()

        ## Text Instructions for the
        ## patrol
        self.infolink = InfoLink(self)
        self.infolink.grid(row = 1, column = 0,sticky="NSEW",columnspan=5)
        self.infolink.grid_remove()

        #buttons for the patrol
        self.prev = tk.Button(self, text="Prev", image=self.IMG_PREV, width=14, height=14,borderwidth=0)
        #self.submit=tk.Button(self, text="Open")
        self.next = tk.Button(self, text="Next", image=self.IMG_NEXT, width=14, height=14,borderwidth=0)
        self.prev.grid(row = 0, column = 1,sticky="W")

        #self.submit.grid(row = 2, column = 1,sticky="NSW")
        self.next.grid(row = 0, column = 4,sticky="E")
        self.next.bind('<Button-1>',self.patrol_next)
        self.prev.bind('<Button-1>',self.patrol_prev)

        self.prev.grid_remove()
        self.next.grid_remove()

        self.excluded = {}

        self.patrol_list = []
        self.capi_update = False
        self.patrol_count = 0
        self.patrol_pos = 0
        self.minutes = 0
        self.isvisible = False
        self.visible()
        self.cmdr = ""
        self.nearest = {}

        self.system = ""

        self.body = ""
        self.lat = ""
        self.lon = ""

        self.started = False

        self.SQID = None #Переменная для хранения информации об
                         #сквадроне пилота

        self.patrol_update()
        self.bind('<<PatrolDisplay>>', self.update_desc)


    def update_desc(self, event):
        self.hyperlink['text'] = "Fetching {}".format(self.patrol_name)
        self.hyperlink['url'] = None


    @classmethod
    def plugin_start(cls,plugin_dir):
        cls.plugin_dir = plugin_dir

    '''
    Every hour we will download the latest data
    '''
    def patrol_update(self):
        UpdateThread(self).start()
        debug('self.after(CYCLE, self.patrol_update)')
        self.after(CYCLE, self.patrol_update)

    def patrol_next(self,event):
        '''
        When the user clicks next it will hide the current patrol for the duration of the session
        It does this by setting an excluded flag on the patrl list
        '''
        #if it the last patrol lets not
        #go any further.
        index = self.nearest.get("index")
        if index + 1 < len(self.patrol_list):
            debug("len {} ind {}".format(len(self.patrol_list),index))
            self.nearest["excluded"] = True
            self.patrol_list[index]["excluded"] = True
            self.update()
            if self.CopyPatrolAdr == 1:
                copyclip(self.nearest.get("system"))
            #if there are excluded
            #closer then we might need
            #to deal with it
            #self.prev.grid()

    def patrol_prev(self,event):
        '''
        When the user clicks next it will unhide the previous patrol
        It does this by unsetting the excluded flag on the previous patrol
        '''
        index = self.nearest.get("index")
        debug("prev {}".format(index))
        if index > 0:
            self.patrol_list[index - 1]["excluded"] = False
            self.update()
            if self.CopyPatrolAdr == 1:
                copyclip(self.nearest.get("system"))


    def update_ui(self,event):
        # rerun every 5 seconds
        debug('in update_ui self.after(5000, self.update_ui)')
        self.after(5000, self.update_ui)
        self.update()

    def update(self):

        if self.visible():

            capi_update = self.patrol_list and self.system and self.capi_update
            journal_update = self.patrol_list and self.system

            if journal_update or capi_update:
                self.sort_patrol()
                p = Systems.edsmGetSystem(self.system)
                self.nearest = self.getNearest(p)
                self.hyperlink['text'] = self.nearest.get("system")
                self.hyperlink['url'] = "https://www.edsm.net/en/system?systemName={}".format(quote_plus(self.nearest.get("system")))

                self.distance['text'] = "{}ly".format(Locale.stringFromNumber(getDistance(p, self.nearest.get("coords")), 2))
                self.infolink['text'] = self.nearest.get("instructions")
                self.infolink['url'] = self.parseurl(self.nearest.get("url"))

                self.infolink.grid()
                self.distance.grid()
                self.prev.grid()
                self.next.grid()
                self.capi_update = False

            else:
                if self.system:
                    self.hyperlink['text'] = "Получение патруля..."
                else:
                    self.hyperlink['text'] = "Ожидание данных о местоположении..."
                self.infolink.grid_remove()
                self.distance.grid_remove()
                self.prev.grid_remove()
                self.next.grid_remove()

    def getStates(self,state_name,bgs):
        sa = []
        active_states = bgs.get(state_name)
        if active_states:
            sa = list(active_states[0].values())

        if sa:
            states = ","
            states = states.join(sa)
            return states
        else:
            return None

    def getBGSInstructions(self,bgs,faction):
        target = 0.50 <= float(bgs.get("influence")) <= 0.65
        over = float(bgs.get("influence")) > 0.65
        under = float(bgs.get("influence")) < 0.50

        if  self.getStates("active_states",bgs):
            statesraw = self.getStates("active_states",bgs).split(",")
            debug(statesraw)
            #statesraw=" States:
            #{}".format(self.getStates("active_states",bgs))
            states = ""

            for i in range(len(statesraw)):
                states = states + ", " + state_list[statesraw[i]]
        else:
            states = ""

        #2019-03-24T11:14:38.000Z
        d1 = datetime.strptime(bgs.get("updated_at"), '%Y-%m-%dT%H:%M:%S.%fZ')
        d2 = datetime.now()

        last_updated = (d2 - d1).days
        if last_updated == 0:
            update_text = ""
        elif last_updated == 1:
            update_text = ". Данные обновлены 1 день назад"
        elif last_updated < 7:
            update_text = ". Последнее обновление данных {} дней назад".format(last_updated)
        elif last_updated > 6:
            update_text = ". Последнее обновление данных {} дней назад. Пожалуйста прыгните в эту систему что бы обновить данные".format(last_updated)

        # if
        # self.getStates("pending_states",bgs):
            # pstates=" Pending:
            # {}".format(self.getStates("pending_states",bgs))
        # else:
            # pstates=""
        if faction == "Close Encounters Corps":
            contact = "Пожалуйста, свяжитесь с AntonyVern [СЕС]#5904 на сервере СЕС для получения инструкций"
        if faction == "EG Union":
            contact = "Пожалуйста, свяжитесь с HEúCMuT#1242 на сервере EGP для получения инструкций"
        if faction == "Royal Phoenix Corporation":
            contact = "Пожалуйста, свяжитесь с Saswitz#9598 на сервере RPSG для получения инструкций"
        #debug(bgs)
        if target:
            retval = "{} Влияние {}%{}{}".format(faction,Locale.stringFromNumber(float(bgs.get("influence") * 100),2),states,update_text)
        if  over:
            retval = "{} Влияние {}%{} {}{}.".format(faction,Locale.stringFromNumber(float(bgs.get("influence") * 100),2),states,contact,update_text)
        if under:
            retval = "{} Влияние {}%{} Пожалуйста выполняйте миссии за {}, чтобы увеличить наше влияние {}".format(faction,Locale.stringFromNumber(float(bgs.get("influence") * 100),2),states,faction,update_text)

        debug("{}: {}".format(bgs.get("system_name"),retval))
        return retval




    def getBGSOveride(self,SQID):
        BGSOveride = []
        SystemsOvireden = []
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQQZFJ4O0nb3L1WJk5oMEPJrr1w5quBSnPRwSbz66XCYx0Lq6aAexm9s1t8N8iRxpdbUOtrhKqQMayY/pub?gid=0&single=true&output=tsv"
        with closing(requests.get(url, stream=True)) as r:
            r.encoding = 'utf-8'
            try:
                reader = csv.reader(r.content.splitlines(), delimiter='\t') # .decode('utf-8')
                next(reader)
            except :
                reader = csv.reader(r.content.decode('utf-8').splitlines(), delimiter='\t') #
                next(reader)
            for row in reader:
                debug(row)
                try:squadron,system,x,y,z,TINF,TFAC,Description = row
                except: error("Detected empty BGS String, please contact VAKazakov/KAZAK0V/Казаков#4700 ASAP")
                bgsSysAndFac = {system:TFAC}
                instructions = Description.format(TFAC,TINF)

                #sysLink=
                #"https://elitebgs.app/system/{}".format()
                if system != '':
                    if squadron == SQID:
                        if  Description != "Basta":
                            self.bgsSystemsAndfactions.update(bgsSysAndFac)  #пока не проверка не валидна, так как
                                                                             #нет модулей для отправки данных
                            SystemsOvireden.append(system)
                            if Description != "Hide" or Description != "Cancel" :
                                try:
                                    BGSOveride.append(newPatrol("BGSO",system,(float(x),float(y),float(z)),instructions,None,None))
                                except:
                                    error("patrol {},{},{},{},{},{},{},{}".format("BGSO",system,x,y,z,instructions,None,None))


                else:
                    error("BGS Overide contains blank lines")

        debug(BGSOveride)
        debug("bgslist is " + str(self.bgsSystemsAndfactions))
        legacy.BGS.bgsTasksSet(self.bgsSystemsAndfactions)
        return BGSOveride, SystemsOvireden



    def getBGSPatrol(self,bgs,faction,BGSOSys):
        debug("bgsDebugSys" + bgs.get("system_name"))
        x,y,z = Systems.edsmGetSystem(bgs.get("system_name"))
        if bgs.get("system_name") in BGSOSys:
            return
        else:
            return newPatrol("BGS",bgs.get("system_name"),(x,y,z),self.getBGSInstructions(bgs,faction),"https://elitebgs.app/system/{}".format(bgs.get("system_id")))




    def getFactionData(self,faction,BGSOSys):
        '''
            We will get Canonn faction data using an undocumented elitebgs api
            NB: It is possible this could get broken so need to contact CMDR Garud
        '''

        patrol = []

        url = "https://elitebgs.app/frontend/factions?name={}".format(faction)
        j = requests.get(url).json()
        if j:
            for bgs in j.get("docs")[0].get("faction_presence"):

                patrol.append(self.getBGSPatrol(bgs,faction,BGSOSys))


        return patrol


    def parseurl(self,url):
        '''
        We will provided some sunstitute variables for the urls
        '''
        if url:
            r = url.replace('{CMDR}',self.cmdr)

            # We will need to
            # initialise to "" if not

            if not self.lat:
                self.lat = ""
            if not self.lon:
                self.lon = ""
            if not self.body:
                self.body = ""

            r = r.replace('{LAT}',str(self.lat))
            r = r.replace('{LON}',str(self.lon))
            r = r.replace('{BODY}',self.body)



            return r
        else:
            return url

    def getJsonPatrol(self,url):
        canonnpatrol = []

        with closing(requests.get(url)) as r:
            reader = r.json()
            for row in reader:

                type = row.get("type")
                system = row.get("system")
                x = row.get("x")
                y = row.get("y")
                z = row.get("z")
                instructions = row.get("instructions")
                url = row.get("url")
                event = row.get("event")
                if system != '':
                    try:
                        canonnpatrol.append(newPatrol(type, system, (float(x), float(y), float(z)), instructions, url, event))
                    except:
                        error("patrol {},{},{},{},{},{},{},{}".format(type, system, x, y, z, instructions, url, event))
                else:
                    error("Patrol contains blank lines")

        return canonnpatrol


    def getTsvPatrol(self,url):

        canonnpatrol = []

        with closing(requests.get(url, stream=True)) as r:
            try:
                reader = csv.reader(r.content.splitlines(), delimiter='\t') # .decode('utf-8')
                next(reader)
            except :
                reader = csv.reader(r.content.decode('utf-8').splitlines(), delimiter='\t') #
                next(reader)
            for row in reader:

                type = get(row,0)
                system = get(row,1)
                x = get(row,2)
                y = get(row,3)
                z = get(row,4)
                instructions = get(row,5)
                url = get(row,6)
                event = get(row,7)
                if system != '':
                    try:
                        canonnpatrol.append(newPatrol(type,system,(float(x),float(y),float(z)),instructions,url,event))
                    except:
                        error("patrol {},{},{},{},{},{},{},{}".format(type,system,x,y,z,instructions,self.parseurl(url),event))
                else:
                    error("Patrol contains blank lines")

        return canonnpatrol

    def getCanonnPatrol(self):
        canonnpatrol = []
        c = 0
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSMFJL2u0TbLMAQQ5zYixzgjjsNtGunZ9-PPZFheB4xzrjwR0JPPMcdMwqLm8ioVMp3MP4-k-JsIVzO/pub?gid=282559555&single=true&output=tsv"
        with closing(requests.get(url, stream=True)) as r:
            try:
                reader = csv.reader(r.content.splitlines(), delimiter='\t') # .decode('utf-8')
                next(reader)
            except :
                reader = csv.reader(r.content.decode('utf-8').splitlines(), delimiter='\t') #
                next(reader)
            for row in reader:
                c = c + 1
                id,	enabled, description, type, link = row
                if enabled == 'Y':
                    if type == 'json':
                        debug("{} Patrol enabled".format(description))
                        canonnpatrol = canonnpatrol + self.getJsonPatrol(link)
                    elif  type == 'tsv':
                        debug("{} Patrol enabled".format(description))
                        canonnpatrol = canonnpatrol + self.getTsvPatrol(link)
                    else:
                        debug("no patrol {}".format(row))
                else:
                    debug("{} Patrol disabled".format(description))


        return canonnpatrol


    def keyval(self,k):
        x,y,z = Systems.edsmGetSystem(self.system)
        return getDistance((x,y,z),k.get("coords"))

    def sort_patrol(self):
        patrol_list = sorted(self.patrol_list, key=self.keyval)


        for num,val in enumerate(patrol_list):
            system = val.get("system")
            type = val.get("type")

            patrol_list[num]["index"] = num


        self.patrol_list = patrol_list


    def SQID_set(self,SQ):
        self.SQID
        if SQ != "":
            self.SQID = SQ
        else: self.SQID = "None"
        debug("SQID In Patrol IS " + self.SQID)

    def download(self):
        #import traceback
        while self.SQID is None:
            debug("Waiting CMDR's squadron {}:\n{}".format(self,""))#traceback.print_stack(Limit=None)
            time.sleep(5)
            if Thread.STOP_ALL:
                return
        debug("Download Patrol Data")

        # if patrol list is populated
        # then was can save
        if self.patrol_list:
            self.save_excluded()
        else:
            self.load_excluded()


        # no point if we have no idea
        # where we are
        if self.system:
            patrol_list = []
            self.bgsSystemsAndfactions = {}
            if self.faction != 1:
                debug("Getting Faction Data")
                BGSO,BGSOSys = self.getBGSOveride(self.SQID)

                try: patrol_list.extend(BGSO)            # Секция, отвечающая за
                                                         # загрузку заданий из
                                                         # гуглофайла
                except: debug("BGS Overide Complete")    #
                debug(BGSO + BGSOSys)
                if self.SQID == "SCEC":
                    try: patrol_list.extend(self.getFactionData("Close Encounters Corps",BGSOSys))       # Секция, отвечающаяя за фракцию
                                                                                                         # 1
                    except: debug("CEC BGS Patrol complete")                                             #
                elif self.SQID == "EGPU":
                    try: patrol_list.extend(self.getFactionData("EG Union",BGSOSys))                     # Секция,
                                                                                                         # отвечающаяя за
                                                                                                         # фракцию 2
                    except: debug("EGP BGS Patrol complete")                                             #
                elif self.SQID == "RPSG":                                                        # Секция
                                                                                                 # шаблон,
                                                                                                 # для
                                                                                                 # применения
                                                                                                 # в
                                                                                                 # случае
                                                                                                 # расширения
                                                                                                 # списка
                                                                                                 # фракций
                                                                                                 # или
                                                                                                 # сообществ
                    try: patrol_list.extend(self.getFactionData("Royal Phoenix Corporation",BGSOSys))                #
                    except: debug("RPSG BGS Patrol complete")
                #elif
                #self.SQID=="Позывной
                #сквадрона": # Секция
                #шаблон, для применения
                #в случае расширения
                #списка фракций или
                #сообществ
                #try:
                #patrol_list.extend(self.getFactionData("Название
                #фракции",BGSOSys)) #
                #except:
                #debug("Название
                #фракции(сокр) BGS
                #Patrol complete") #
                if None in patrol_list:
                    while None in patrol_list:
                        patrol_list.remove(None)
                    debug("None Patrols cleared")

            if self.ships and self.HideMyShips != 1:
                patrol_list.extend(self.ships)

            if self.canonn != 1:
                self.canonnpatrol = self.getCanonnPatrol()
                patrol_list.extend(self.canonnpatrol)

            if self.edsm != 1:
                patrol_list.extend(self.getEDSMPatrol())

            # add exclusions from configuration
            for num,val in enumerate(patrol_list):
                system = val.get("system")
                type = val.get("type")

                if self.excluded.get(type):
                    if self.excluded.get(type).get(system):
                        patrol_list[num]["excluded"] = self.excluded.get(type).get(system)

            # we will sort the patrol list
            self.patrol_list = patrol_list
            self.sort_patrol()

            debug("download done")
            self.started = True
            # poke an evennt safely
            self.event_generate('<<PatrolDone>>', when='tail')


    def getEDSMPatrol(self):
        url = "https://www.edsm.net/en/galactic-mapping/json"

        types = {
            'minorPOI': 'Minor Point of Interest',
            'planetaryNebula': 'Planetary Nebula',
            'nebula': 'Nebula',
            'blackHole': 'Black Hole',
            'historicalLocation': 'Historical Location',
            'stellarRemnant': 'Stellar Remnant',
            'planetFeatures': 'Planet Features',
            'regional': 'Regional',
            'pulsar': 'Pulsar',
            'starCluster': 'Star Cluster',
            'jumponiumRichSystem': 'Jumponium Rich System',
            'surfacePOI': 'Surface Point of Interest',
            'deepSpaceOutpost': 'Deep Space Outpost',
            'mysteryPOI': 'Mystery Point of Interest',
            'organicPOI': 'Organic Point of Interest',
            'restrictedSectors': 'Restricted Sector',
            'geyserPOI': 'Geyser Point of Interest',
            'region': 'Region',
            'travelRoute': 'Travel Route',
            'historicalRoute': 'Historical Route',
            'minorRoute': 'Minor Route',
            'neutronRoute': 'Neutron Route'
        }

        validtypes = ['minorPOI', 'planetaryNebula', 'nebula', 'blackHole', 'historicalLocation', 'stellarRemnant',
                      'planetFeatures', 'regional', 'pulsar', 'starCluster', 'jumponiumRichSystem', 'surfacePOI',
                      'deepSpaceOutpost', 'mysteryPOI', 'organicPOI', 'restrictedSectors', 'geyserPOI']

        r = requests.get(url)
        r.encoding = 'utf-8'
        debug(r.encoding)
        entries = r.json()
        categories = {}

        edsm_patrol=[]

        self.patrol_name = "Galactic Mapping"

        for entry in entries:

            if entry.get("type") in validtypes and "Archived: " not in entry.get("name"):

                edsm_patrol.append(
                    newPatrol("Galactic Mapping",
                            entry.get("galMapSearch"), (
                                float(entry.get("coordinates")[0]),
                                float(entry.get("coordinates")[1]),
                                float(entry.get("coordinates")[2])
                            ),
                              "Galactic Mapping Project: {} : {}".format(types.get(entry.get("type")),entry.get("name").encode('utf-8')),
                              entry.get("galMapUrl"),
                              None)
                )

        self.event_generate('<<PatrolDone>>', when='tail')
        return edsm_patrol

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.canonnbtn = tk.IntVar(value=config.getint("HidePatrol"))
        self.factionbtn = tk.IntVar(value=config.getint("Hidefactions"))
        self.hideshipsbtn = tk.IntVar(value=config.getint("HideMyShips"))
        self.edsmbtn = tk.IntVar(value=config.getint("HideEDSM"))
        self.copypatrolbtn = tk.IntVar(value=config.getint("CopyPatrolAdr"))

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.HideMyShips = self.hideshipsbtn.get()
        self.edsm = self.edsmbtn.get()
        self.CopyPatrolAdr = self.copypatrolbtn.get()



        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row = gridrow, column = 0,sticky="NSEW")

        nb.Label(frame,text="Настройки патруля").grid(row=0,column=0,sticky="NW")
        nb.Checkbutton(frame, text="Скрыть патруль", variable=self.canonnbtn).grid(row = 1, column = 0,sticky="NW")
        nb.Checkbutton(frame, text="Скрыть BGS", variable=self.factionbtn).grid(row = 1, column = 1,sticky="NW")
        nb.Checkbutton(frame, text="Скрыть данные ваших кораблей", variable=self.hideshipsbtn).grid(row = 2, column = 1,sticky="NW")
        nb.Checkbutton(frame, text="Скрыть Galactic Mapping POI", variable=self.edsmbtn).grid(row=2, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Автоматически копировать \nпатруль в буфер обмена", variable=self.copypatrolbtn).grid(row = 3, column = 0,sticky="NW",)


        debug("canonn: {}, faction: {} hideships {}, EDSM {}".format(self.canonn, self.faction, self.HideMyShips, self.edsm))

        return frame

    def visible(self):

        nopatrols = self.canonn == 1 and self.faction == 1 and self.HideMyShips == 1 and self.edsm == 1

        if nopatrols:
            self.grid_remove()
            self.isvisible = False
            return False
        else:
            self.grid()
            self.isvisible = True
            return True

    def getNearest(self,location):
        nearest = ""
        for num,patrol in enumerate(self.patrol_list):
            # add the index to the
            # patrol so we can navigate
            self.patrol_list[num]["index"] = int(num)

            if not patrol.get("excluded"):
                if nearest != "":

                    if getDistance(location,patrol.get("coords")) < getDistance(location,nearest.get("coords")):
                        nearest = patrol

                else:

                    nearest = patrol


        return nearest


    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('HidePatrol', self.canonnbtn.get())
        config.set('Hidefactions', self.factionbtn.get())
        config.set('HideMyShips', self.hideshipsbtn.get())
        config.set('HideEDSM', self.edsmbtn.get())
        config.set('CopyPatrolAdr', self.copypatrolbtn.get())

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.HideMyShips = self.hideshipsbtn.get()
        self.edsm = self.edsmbtn.get()
        self.CopyPatrolAdr = self.copypatrolbtn.get()

        if self.visible():
            # we should fire off an
            # extra download
            UpdateThread(self).start()


        debug("canonn: {}, faction: {} hideships {} hideEDSM {}".format(self.canonn, self.faction, self.HideMyShips, self.edsm))

    def trigger(self,system,entry):
        # exit if the events dont match

        event = json.loads(self.nearest.get("event"))
        debug("event {}".format(event))
        for key in list(event.keys()):
            if event.get(key):
                debug("event key {} value {}".format(key,event.get(key)))
                if not str(entry.get(key)).upper() == str(event.get(key)).upper():
                    return False

        debug("triggered")
        #autosubmit the form --
        #allowing for google forms
        if self.nearest.get("url"):
            j = requests.get(self.nearest.get("url").replace('viewform','formResponse'))
        self.patrol_next(None)



    def journal_entry(self,cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
        # We don't care what the
        # journal entry is as long as
        # the system has changed.

        self.body = body
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.z = z

        if system and not self.started:
            debug("Patrol download cycle commencing")
            self.started = True
            self.patrol_update()

        if cmdr:
            self.cmdr = cmdr

        if self.system != system and entry.get("event") in ("Location","FSDJump","StartUp") :
            debug("Refresshing Patrol ({})".format(entry.get("event")))
            self.system = system
            self.update()
            if self.nearest and self.CopyPatrolAdr == 1:
                copyclip(self.nearest.get("system"))
        if body:
            self.update()
        # else:
            # error("nope
            # {}".format(entry.get("event")))
            # error(system)
            # error(self.system)

        #If we have visted a system and
        #then jump out then lets
        #clicknext
        if system and self.nearest:
            if self.nearest.get("system").upper() == system.upper() and entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
                self.patrol_next(None)

        #After we have done everything
        #else let's see if we can
        #automatically submit and move
        #on
        if system and self.nearest.get("event") and self.nearest.get("system").upper() == system.upper():
            self.trigger(system,entry)





    def load_excluded(self):
        debug("loading excluded")
        self.patrol_config = os.path.join(Release.plugin_dir,'data','EDMC-Triumvirate.patrol')
        try:
            with open(self.patrol_config) as json_file:
                self.excluded = json.load(json_file)
        except:
            pass #debug("no config file {}".format(self.patrol_config))


    def save_excluded(self):
        self.patrol_config = os.path.join(Release.plugin_dir,'data','EDMC-Triumvirate.patrol')
        excluded = {}
        for patrol in self.patrol_list:
            if patrol.get("excluded") and not patrol.get("type") in ('BGS','SHIPS'):
                if not excluded.get(patrol.get("type")):
                    excluded[patrol.get("type")] = {}
                excluded[patrol.get("type")][patrol.get("system")] = True


        with open(self.patrol_config, 'w+') as outfile:
            json.dump(excluded, outfile)

    def plugin_stop(self):
        '''
        When the plugin stops we want to save the patrols where excluded = True
        We will not inclde ships or BGS in this as they can be excluded in other ways.
        '''
        self.save_excluded()

    def cmdr_data(self,data, is_beta):
        """
        We have new data on our commander

        Lets get a list of ships
        """
        self.cmdr = data.get('commander').get('name')

        self.ships = []
        self.system = data.get("lastSystem").get("name")

        current_ship = data.get("commander").get("currentShipId")

        shipsystems = {}

        #debug(json.dumps(data.get("ships"),indent=4))

        for ship in list(data.get("ships").keys()):

            if int(ship) != int(current_ship):
                ship_system = data.get("ships").get(ship).get("starsystem").get("name")
                if not shipsystems.get(ship_system):
                    debug("first: {}".format(ship_system))
                    shipsystems[ship_system] = []
                #else:
                #    debug("second:
                #    {}".format(ship_system))

                shipsystems[ship_system].append(data.get("ships").get(ship))
                #if ship_system ==
                #"Celaeno":
                #    debug(json.dumps(shipsystems[ship_system],indent=4))
            #else:
                #debug("skipping
                #{}".format(ship))

        for system in list(shipsystems.keys()):
            ship_pos = Systems.edsmGetSystem(system)
            ship_count = len(shipsystems.get(system))
            #if system == "Celaeno":
            #    debug(json.dumps(shipsystems.get(system),indent=4))
            if ship_count == 1:
                #debug(shipsystems.get(system))
                ship_type = getShipType(shipsystems.get(system)[0].get("name"))
                ship_name = shipsystems.get(system)[0].get("shipName")
                ship_station = shipsystems.get(system)[0].get("station").get("name")
                ship_info = "Ваш{}, {} пристыкован(а) к {}".format(ship_type,ship_name,ship_station)
            elif ship_count == 2:

                if shipsystems.get(system)[0].get("station").get("name") == shipsystems.get(system)[1].get(
                    "station").get("name"):
                    ship_info = "Ваш{} ({}) и ваш{} ({}) пристыкованы к {}".format(
                        getShipType(shipsystems.get(system)[0].get("name")),
                        getShipType(shipsystems.get(system)[0].get("shipName")),
                        getShipType(shipsystems.get(system)[1].get("name")),
                        getShipType(shipsystems.get(system)[1].get("shipName")),
                        shipsystems.get(system)[0].get("station").get("name"))
                    #debug(ship_info)
                else:

                    ship_info = "Ваш{} ({}) пристыкован(а) к {} и ваш{} ({}) пристыкован к {}".format(
                        getShipType(shipsystems.get(system)[0].get("name")),
                        getShipType(shipsystems.get(system)[0].get("shipName")),
                        shipsystems.get(system)[1].get("station").get("name"),
                        getShipType(shipsystems.get(system)[1].get("name")),
                        getShipType(shipsystems.get(system)[1].get("shipName")),
                        shipsystems.get(system)[0].get("station").get("name"))
                    #debug(ship_info)
            else:
                ship_info = "У вас {} кораблей в этой системе".format(ship_count)
                #debug(ship_info)

            self.ships.append(newPatrol("SHIPS",system,ship_pos,ship_info,None))

        self.capi_update = True
        if self.system and not self.started:
            debug("Patrol download cycle commencing")
            self.started = True
            self.patrol_update()


def copyclip(value):
    debug("copyclip")
    window = tk.Tk()
    window.withdraw()
    window.clipboard_clear()  # clear clipboard contents
    window.clipboard_append(value)
    debug("copyclip_append")
    window.update()
    window.destroy()
    debug("copyclip done")


def getDistance(p, g):
    # gets the distance between two systems
    return math.sqrt(sum(tuple([math.pow(p[i] - g[i], 2) for i in range(3)])))


def newPatrol(type, system, coords, instructions, url, event = None):
    return {
        "type": type,
        "system": system,
        "coords": coords,
        "instructions": instructions,
        "url": url,
        "event": event,
    }
