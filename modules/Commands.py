
# -*- coding: utf-8 -*- 
import Discord
import load
import datetime
from debug import debug
def sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons):
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
    if state["ShipType"]=="SRV":
        return ("SOS отключена, пока вы в СРВ")
    if DistFromStarLS is not None:
        Distance=unicode(u",\n"+unicode(DistFromStarLS)+u" Св.Сек.")
    else:   Distance=unicode("")
    LifeSupport=state["Modules"]['LifeSupport']['Item']
    if (fuel["FuelMain"]+fuel["FuelReservoir"])!=0:
        if fuel_cons!=0 :
            sec_to_go=(fuel["FuelMain"]+fuel["FuelReservoir"])/fuel_cons
        
            time_to_go=datetime.timedelta(seconds=sec_to_go)

            params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Требуется заправка"),
                        "EColor":"16776960",
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        "Foouter":"Расчетное время отключения:"  ,
                        "Timestamp":(time_to_go),
                        "params":{
                            unicode(u"Местоположение:"):unicode(system+Distance),
                            unicode(u"Топлива осталось:"):unicode(str(fuel["FuelMain"]+fuel["FuelReservoir"])+u" тонн"),
                            unicode(u"Времени до отключения:"):unicode(time_to_go),
                            }})
        else:
            params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Требуется заправка"),
                        "EColor":"16776960",
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        
                        
                        "params":{
                            unicode(u"Местоположение:"):unicode(system+Distance),
                            unicode(u"Топлива осталось:"):unicode(str(fuel["FuelMain"]+fuel["FuelReservoir"])+u" тонн"),
                            unicode(u"Времени до отключения:"):unicode(u"Не кончится"),
                            }})
    else: params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Срочно требуется топливо, произведено отключение всех систем!!!"),
                        "EColor":"16711680",
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        "Foouter":unicode("Расчетное время смерти:"),
                        "Timestamp":(time_to_go),
                        "params":{
                            unicode(u"Местоположение:"):unicode(system+", "+Distance),
                            unicode(u"Топлива осталось:"):unicode(str(fuel["FuelMain"]+fuel["FuelReservoir"])+u" тонн"),
                            unicode(u"Кислород кончится через (прим.):"):LifeSupportList[LifeSupport],
                            }})
    Discord.Sender(cmdr,"FuelAlarm",params)
    return "Сигнал о помощи послан, ожидайте"
          


def commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,fuel,fuel_cons):
    if entry['event']=="SendText":
        if entry['Message'].lower()=='/sos':
            return sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons)   