
# -*- coding: utf-8 -*- 
import Discord
import load
from debug import debug
def sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel):
    debug("Sos Initiated")
    params={}
    #fuel=load.fuel
    LifeSupport=state["Modules"]['LifeSupport']['Item']
    params.update({"Etitle":"SOS",
                        "EDesc":"requesting help",
                        "EColor":"242424",
                        "params":{
                            "Location":system+", "+str(DistFromStarLS),
                            "Fuel left":str(fuel["FuelMain"]+fuel["FuelReservoir"]),
                            "Time to oxigen depleting":LifeSupport}})
    Discord.Sender(cmdr,"FuelAlarm",params)
          


def commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,fuel):
    if entry['event']=="SendText":
        debug("command? "+str(entry["Message"]))
        debug("com? "+str(entry["Message"]=='!sos'))
        if entry['Message']=='!sos':
            debug("SOS?")
            sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel)   