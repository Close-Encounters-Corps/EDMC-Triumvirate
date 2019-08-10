
# encoding = utf-8

from __future__ import unicode_literals


from legacy import Reporter


import threading
import requests
from urllib import quote_plus
import sys
from  math import sqrt,pow,trunc
from debug import Debug
from debug import debug,error


class BGS(object):
    def __init__(self):
        self.bgsTasks = {}
    DefaultFacts={"SCEC":"Close Encounter Corps"}
    FormsAddrs={                     #https://docs.google.com/forms/     formResponse?usp=pp_url
                    "SCEC":{
                        "FactionKillBond" : {"addr":"d/e/1FAIpQLSelyvxTug3VXv8S_eRLRg85O_OOTKUHxDSkhfZnT-pLCfOl0w/","cmdr":"&entry.1208677263=","system":"&entry.479281488=","Reward":"&entry.21740167=","AwardingFaction":"&entry.828342601=","VictimFaction":"&entry.82740214=PS4"},

                        }
                    ,} 
    FactFormsAddr = {}
    Exlude=True
    @classmethod
    def SQID_set(cls,SQ):
        if SQ== "N/A":
            cls.Exlude=True
        if SQ != "":
            try:
                cls.FactFormsAddr=cls.FormsAddrs[SQ]
                cls.Exlude=False
            except KeyError:
                cls.Exlude=True
            try:cls.DefaultFacts=str(cls.DefaultFacts[SQ])
            except:cls.DefaultFacts=None        
        
    
    @classmethod
    def bgsTasksSet(cls,bgsTask):
        cls.bgsTasks = bgsTask
        debug("Override is "+str(cls.bgsTasks))

    def EventRead(self,cmdr, is_beta, system, station, entry, client):
        debug("BGSSend Commence")
        if self.Exlude == True :
            return
        debug("BGSSend not excluded")
        if entry["event"] == "MissionCompleted" or entry["event"] == "SellExplorationData" or entry["event"] == "MultiSellExplorationData" or entry["event"] == "RedeemVoucher" or entry["event"]=="FactionKillBond":
            try:debug("BGSSend stage1 "+str(system in self.bgsTasks or self.DefaultFacts in entry))
            except:pass
            if system in self.bgsTasks or self.DefaultFacts in entry:
                debug("BGSSend stage 2")
                if entry["event"] == "FactionKillBond" :
                    if entry["AwardingFaction"] in self.bgsTasks[system] or  entry["AwardingFaction"]==self.DefaultFacts:
                        Addr=FactFormsAddr["FactionKillBond"]

                        url = "https://docs.google.com/forms/"+Addr["addr"]+"formResponse?usp=pp_url"
                        url+= Addr["cmdr"]+quote_plus(cmdr)
                        url+= Addr["system"]+quote_plus(system)
                        url+= Addr["Reward"]+quote_plus(entry["Reward"])
                        url+= Addr["AwardingFaction"]+quote_plus(entry["AwardingFaction"])
                        url+= Addr["VictimFaction"]+quote_plus(entry["VictimFaction"])
                        Reporter(url).start()

            #if system in self.bgsTasks:
            #url = 'https://docs.google.com/forms/d/e/1FAIpQLSd1HNysgZRf4p0_I_hHxbwWz4N8EFEWtjsVaK9wR3RB66kiTQ/formResponse?usp=pp_url'
            #url+='&entry.2038615400=' + quote_plus(cmdr)
            #url+='&entry.1807008459=' + quote_plus(entry["event"])
            #url+='&entry.569295685=' + quote_plus(str(entry))
            #debug("BGS TESTS " + url)
            #Reporter(url).start()

        #if "MissionCompleted" in entry or "SellExplorationData" in entry or
        #"MultiSellExplorationData" in entry or "RedeemVoucher" in entry:
        #    if system in self.bgsTasks:
        #        if "MissionCompleted" in entry:
        #            if factionMatch and 'Reward' in entry:
        #                url='https://docs.google.com/forms/d/e/1FAIpQLSdA-iypOHxi5L4iaINr57hVJYWaZj9d-rmx_rpLJ8mwPrlccQ/formResponse?usp=pp_url'
        #                url+='&entry.1574172588='+quote_plus(cmdr)
        #                if is_beta:
        #                    beta='Y'
        #                else:
        #                    beta='N'
        #                url+='&entry.1534486210='+quote_plus(beta)
        #                url+='&entry.451904934='+quote_plus(system)
        #                if station is not None:
        #                    url+='&entry.666865209='+quote_plus(station)
                    
        #                url+='&entry.310344870='+str(entry['Reward'])
        #                url+='&entry.706329985='+quote_plus(entry['AwardingFaction'])
        #                url+='&entry.78713015='+quote_plus(entry['VictimFaction'])
        #                Reporter(url).start()
        #        if "SellExplorationData" in entry:
        #            None
        #        if "MultiSellExplorationData" in entry:
        #            None
        #        if "RedeemVoucher" in entry:
                   # None
                #if "ACTION NAME(LOGS)" in entry:
                #   None
