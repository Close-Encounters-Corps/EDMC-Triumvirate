
# -*- coding: utf-8 -*- 
import Discord
import load
from debug import debug
def sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel):
    LifeSupportList={
        "int_lifesupport_size1_class1":"5:00",
"int_lifesupport_size1_class2":"7:30",
"int_lifesupport_size1_class3":"10:00",
"int_lifesupport_size1_class4":"15:00",
"int_lifesupport_size1_class5":"25:00",
"int_lifesupport_size2_class1":"5:00",
"int_lifesupport_size2_class2":"7:30",
"int_lifesupport_size2_class3":"10:00",
"int_lifesupport_size2_class4":"15:00",
"int_lifesupport_size2_class5":"25:00",
"int_lifesupport_size3_class1":"5:00",
"int_lifesupport_size3_class2":"7:30",
"int_lifesupport_size3_class3":"10:00",
"int_lifesupport_size3_class4":"15:00",
"int_lifesupport_size3_class5":"25:00",
"int_lifesupport_size4_class1":"5:00",
"int_lifesupport_size4_class2":"7:30",
"int_lifesupport_size4_class3":"10:00",
"int_lifesupport_size4_class4":"15:00",
"int_lifesupport_size4_class5":"25:00",
"int_lifesupport_size5_class1":"5:00",
"int_lifesupport_size5_class2":"7:30",
"int_lifesupport_size5_class3":"10:00",
"int_lifesupport_size5_class4":"15:00",
"int_lifesupport_size5_class5":"25:00",
"int_lifesupport_size6_class1":"5:00",
"int_lifesupport_size6_class2":"7:30",
"int_lifesupport_size6_class3":"10:00",
"int_lifesupport_size6_class4":"15:00",
"int_lifesupport_size6_class5":"25:00",
"int_lifesupport_size7_class1":"5:00",
"int_lifesupport_size7_class2":"7:30",
"int_lifesupport_size7_class3":"10:00",
"int_lifesupport_size7_class4":"15:00",
"int_lifesupport_size7_class5":"25:00",
"int_lifesupport_size8_class1":"5:00",
"int_lifesupport_size8_class2":"7:30",
"int_lifesupport_size8_class3":"10:00",
"int_lifesupport_size8_class4":"15:00",
"int_lifesupport_size8_class5":"25:00",}
    debug("Sos Initiated")
    params={}
    #fuel=load.fuel
    LifeSupport=state["Modules"]['LifeSupport']['Item']
    params.update({"Etitle":"SOS",
                        "EDesc":"requesting help",
                        "EColor":"16711680",
                        "params":{
                            "Location":system+", "+str(DistFromStarLS),
                            "Fuel left":str(fuel["FuelMain"]+fuel["FuelReservoir"]),
                            "Time to oxigen depleting":LifeSupportList[LifeSupport]}})
    Discord.Sender(cmdr,"FuelAlarm",params)
          


def commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,fuel):
    if entry['event']=="SendText":
        debug("command? "+str(entry["Message"]))
        debug("com? "+str(entry["Message"]=='!sos'))
        if entry['Message']=='!sos':
            debug("SOS?")
            sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel)   