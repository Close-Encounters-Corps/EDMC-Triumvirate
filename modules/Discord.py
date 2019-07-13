
# -*- coding: utf-8 -*- 

import load
from discord_webhook import    DiscordWebhook, DiscordEmbed
import sys
from debug import debug

import logging
logging.basicConfig()


#this = sys.modules[__name__]

contentlist={
        "EGPU":
            {
                "FuelAlarm":"<@&597996086959013900>",
                #"ActionName":"WebhoouAdr",
            },
       "SCEC":
            {
                "FuelAlarm":"",
                "Example":"",
            } ,
       "RPSG":
           {
                "FuelAlarm":"<@&524926198560587777>",

           },
       }

webhookList={
        "EGPU":
            {
                "FuelAlarm":"",
                #"ActionName":"WebhoouAdr",
            },
       "SCEC":
            {
                "FuelAlarm":"599634967768596490/FbNF1iE1pK-s3EZ9Q0Vg6VBdsGPUKO4nMtaYNmYrYQpmsN9QK-xkOvMtbDHtYy7SVQMM",
                "Example":"599240932663230505/HGgJcfmqPwLvDXh4z6mZ1gBUq7TQkBvy4YrvfHsPjeGlgktgma8ZcHXDiG10OgUYKFMu",
            } ,
       "RPSG":
           {
                "FuelAlarm":"599627968112885787/9AC__aLYB8qsxC2ioWoGLLmyomDWNCRVHF2M9QTtlaNygZ97b1R-Bc4yTWYsPhJfy5Z5",

           },
       }
#class Send:
    
   #def __init__(SQ):
        
SQID=""       
def SQID_set(SQ):
        global SQID
        if SQ != "":
            SQID=SQ
        else: SQID="None"
        debug("SQID DIS"+SQID)



def send(cmdr,action,params):    #

        '''
        cmdr- User of Plugin
        action- name of webhook
        params - dist of parametrs
        '''
        #SQID=load.SQID

        debug("Webhook Initiatet")
        debug(SQID)
        #if webhookList[SQID][action] =="None":
        #    return
        webhook = DiscordWebhook(url='https://discordapp.com/api/webhooks/{}'.format(webhookList[SQID][action]),                        #.format(webhookList[SQID][action]
                                username=action,
                                avatar_url=params["Avatar"] ,
                                content= contentlist[SQID][action])
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