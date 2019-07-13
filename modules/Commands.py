
# -*- coding: utf-8 -*- 
import Discord
import load
import datetime
from debug import debug
def sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons,SQID):
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
    time_to_go=datetime.timedelta(seconds=(fuel["FuelMain"]+fuel["FuelReservoir"])/fuel_cons)
    
    LifeSupport=state["Modules"]['LifeSupport']['Item']
    params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Требуется заправка"),
                        "EColor":"16711680",
                        "Avatar":"https://cdn.discordapp.com/attachments/518418556615000074/599610037773664276/kisspng-stop-sign-clip-art-sos-5ac4dd7ef16d32.png",
                        "params":{
                            unicode(u"Местоположение:"):system+", "+unicode(DistFromStarLS),
                            unicode(u"Топлива осталось:"):unicode(str(fuel["FuelMain"]+fuel["FuelReservoir"])+u" тонн"),
                            #"Time to oxigen depleting":LifeSupportList[LifeSupport],
                            unicode(u"Времени до отключения:"):unicode(time_to_go),
                            }})
    Discord.Sender(cmdr,"FuelAlarm",params)
          


def commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,fuel,fuel_cons,SQID):
    if entry['event']=="SendText":
        if entry['Message'].lower()=='/sos':
            
            sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons,SQID)   