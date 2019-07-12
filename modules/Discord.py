
# -*- coding: utf-8 -*- 

import load
from discord_webhook import    DiscordWebhook, DiscordEmbed
import sys
from debug import debug

import logging
logging.basicConfig()


#this = sys.modules[__name__]



webhookList={
        "EGPU":
            {
            "FuelAlarm":"",
            #"ActionName":"WebhoouAdr",
            },
       "SCEC":
            {
            "FuelAlarm":"",
            "Example":"599240932663230505/HGgJcfmqPwLvDXh4z6mZ1gBUq7TQkBvy4YrvfHsPjeGlgktgma8ZcHXDiG10OgUYKFMu",
            } ,
       }
class Send:
    
   #def __init__(SQ):
        
        
    



    def send(self,cmdr,action,params):    #

        '''
        cmdr- User of Plugin
        action- name of webhook
        params - dist of parametrs
        '''
        self.SQID=load.SQID
        debug("Webhook Initiatet"+self.SQID)
        self.webhook = DiscordWebhook(url='https://discordapp.com/api/webhooks/599240932663230505/HGgJcfmqPwLvDXh4z6mZ1gBUq7TQkBvy4YrvfHsPjeGlgktgma8ZcHXDiG10OgUYKFMu',                        #.format(webhookList[SQID][action]
                                username=action,
                                content='<@264863927265918976>' )
        self.embed = DiscordEmbed(title=params["Etitle"], description=params["EDesc"], color=params["EColor"])
        self.embed.set_author(name=cmdr)
        #self.embed.set_footer(text=)
        self.embed.set_timestamp()
        for key, entry  in params["params"].iteritems():
            debug("webhook"+key+entry)
            self.embed.add_embed_field(name=key, value=entry)
            
            
        debug(self.embed)
        self.webhook.add_embed(self.embed)
        debug(self.webhook)
        self.webhook.execute()

def Sender(cmdr,action,params):
     Send.send(cmdr,action,params)
'''
       Discord.Sender("KAZAK0V","FuelAlarm",{
            "Etitle":"SOS",
            "EDesc":"requesting help",
            "EColor":"242424",
            "params":{
                "Location":"Jataya",
                "Fuel left":"1.0234 tonns",
                "Time to oxigen depleting":"25:00"}})
''' 