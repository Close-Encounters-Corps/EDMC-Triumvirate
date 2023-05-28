# -*- coding: utf-8 -*-
try:
    from .discord_webhook import DiscordWebhook, DiscordEmbed
except:
    from discord_webhook import DiscordWebhook, DiscordEmbed
import sys
from .debug import debug
import datetime

import time

from .lib.context import global_context

# this = sys.modules[__name__]
contentlist = {
    "EGPU": {
        "FuelAlarm": "<@&597996086959013900>",
        # "ActionName":"WebhoouAdr",
    },
    "SCEC": {
        "FuelAlarm": "Штатный пилот Close Encounters Corps запрашивает дозаправку!\n ",  # <@&589109509843320852>
        # <@&589110175668109317>
        # <@&301455749874188289>
        "Dev": "",
    },
    "RPSG": {"FuelAlarm": "<@&524926198560587777>",},
    "N/A": {
        "FuelAlarm": "Независимый пилот запрашивает помощь!\n<@&589109509843320852> <@&589110175668109317> <@&301455749874188289> ",
    },
    "TEST": {"FuelAlarm": "Тест системы оповещения"},
}

webhookList = {
    "EGPU": {
        "FuelAlarm": "600027420392685599/OKcfg9XfGPDQb4WKVWkhQ9kqpzPXtQlcMLc7W-lTP0OOVxuLyrtHGO1bzjPdIgjjgqtN",
        # "ActionName":"WebhoouAdr",
    },
    "SCEC": {
        "FuelAlarm": "600259766660366346/7hvYrjMJn1xhsCffXpmN2I8qqh5jSuFqUaPeZ9WRAcMqbaTLm4We9MYMr6P-ceC5wh3Q",
    },
    "RPSG": {
        "FuelAlarm": "599627968112885787/9AC__aLYB8qsxC2ioWoGLLmyomDWNCRVHF2M9QTtlaNygZ97b1R-Bc4yTWYsPhJfy5Z5",
    },
    "N/A": {
        "FuelAlarm": "600259766660366346/7hvYrjMJn1xhsCffXpmN2I8qqh5jSuFqUaPeZ9WRAcMqbaTLm4We9MYMr6P-ceC5wh3Q",
    },
    "TEST": {
        "FuelAlarm": "600260403414695936/o9iz7Ow-TfInwOKvCH5ipwzRXlbr7B5QXlV_AjR74LXJ8QnOY4UV8qV3371clTp20wb1"
    },
}

def send(cmdr, action, params):
    """
    cmdr- User of Plugin
    action- name of webhook
    params - dist of parametrs
    """
    SQID = global_context.SQ
    debug("Webhook Initiated")
    if SQID not in webhookList:
        return "Вам недоступно данное действие"
    webhook = DiscordWebhook(
        url="https://discordapp.com/api/webhooks/{}".format(
            webhookList[SQID][action]
        ),  # .format(webhookList[SQID][action]
        username=action,
        avatar_url=params["Avatar"],
        content=contentlist[SQID][action],
    )
    if params["Embed?"]:
        embed = DiscordEmbed(
            title=params["Etitle"], description=params["EDesc"], color=params["EColor"]
        )
        embed.set_author(name=cmdr)
        # embed.set_footer(text=)
        if "Foouter" in params:
            embed.set_footer(text=params["Foouter"])
        if "Timestamp" in params:
            embed.set_timestamp(
                str(
                    datetime.datetime.utcfromtimestamp(time.time())
                    + params["Timestamp"]
                )
            )
        else:
            embed.set_timestamp()
        for key, entry in params["Fields"].items():
            # debug("webhook"+unicode(key)+unicode(entry))
            embed.add_embed_field(name=key, value=entry)

        # debug(embed)
        webhook.add_embed(embed)
    debug("Webhook sended")
    webhook.execute()


def Sender(cmdr, action, params):
    """
    :param cmdr: User of plugin, which will be thrown to embeds\webhook name (depend of action name)
    :param action: name of webhook, also depend to webhook adr
    :param params: dist of parametrs :
        {"Embed?":True\False, #if False, embed will not be created
        "Etitle":unicode, #set name for Embed,
        "EDesc":unicode, #sets description for Embed,
        "EColor":int or str, #contains int, this will set set color for embed,
        "Foouter":unicode, #optional
        "Timestamp": #optional,Time till something
        "Fields":{ #dict of pairs FieldName/FieldValues
            "Location":"Jataya",
            "Fuel left":"1.0234 tonns",
            "Time to oxigen depleting":"25:00"}}
    """
    send(cmdr, action, params)
