
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
#class Send:
    
   #def __init__(SQ):
        
        
    



def send(cmdr,action,params):    #

        '''
        cmdr- User of Plugin
        action- name of webhook
        params - dist of parametrs
        '''
        #SQID=load.SQID
        debug("Webhook Initiatet")
        webhook = DiscordWebhook(url='https://discordapp.com/api/webhooks/599240932663230505/HGgJcfmqPwLvDXh4z6mZ1gBUq7TQkBvy4YrvfHsPjeGlgktgma8ZcHXDiG10OgUYKFMu',                        #.format(webhookList[SQID][action]
                                username=action,
                                avatar_url="https://cdn.discordapp.com/attachments/518418556615000074/599610037773664276/kisspng-stop-sign-clip-art-sos-5ac4dd7ef16d32.png" ,
                                content='<@264863927265918976>' )
        embed = DiscordEmbed(title=params["Etitle"], description=params["EDesc"], color=params["EColor"])
        embed.set_author(name=cmdr)
        #embed.set_footer(text=)
        embed.set_timestamp()
        for key, entry  in params["params"].iteritems():
            #debug("webhook"+unicode(key)+unicode(entry))
            embed.add_embed_field(name=key, value=entry)
            
            
        #debug(embed)
        webhook.add_embed(embed)
        debug(webhook)
        webhook.execute()

def Sender(cmdr,action,params):
     send(cmdr,action,params)
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