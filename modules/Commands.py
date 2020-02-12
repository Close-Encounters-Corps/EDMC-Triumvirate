
# -*- coding: utf-8 -*-
from . import Discord

import datetime
from .debug import debug


def sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons,is_SRV,is_Fighter):
    LifeSupportList = {
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
    FuelReserwours = {
								"sidewinder":0.3,
        "eagle":0.34,
        "hauler":0.25,
        "adder":0.36,
        "empire_eagle":0.37,
        "viper":0.41,
        "cobramkiii":0.49,
        "viper_mkiv":0.46,
        "diamondback":0.49,
        "cobramkiv":0.51,
        "type6":0.39,
        "dolphin":0.5,
        "diamondbackxl":0.52,
        "empire_courier":0.41,
        "independant_trader":0.39,
        "asp_scout":0.47,
        "vulture":0.57,
        "asp":0.63,
        "federation_dropship":0.83,
        "type7":0.52,
        "typex":0.77,
        "federation_dropship_mkii":0.72,
        "empire_trader":0.74,
        "typex_2":0.77,
        "typex_3":0.77,
        "federation_gunship":0.82,
        "krait_light":0.63,
        "krait_mkii":0.63,
        "orca":0.79,
        "ferdelance":0.67,
        "mamba":0.5,
        "python":0.83,
        "type9":0.77,
        "belugaliner":0.81,
        "type9_military":0.77,
        "anaconda":1.07,
        "federation_corvette":1.13,
        "cutter":1.16,}
    debug("Sos Initiated")
    params = {}
    #fuel=load.fuel
    
    if state['Role'] != None: return "Вы находитесь в экипаже, SOS отключено" # Эта команда прервет выполнение, если
                                                                              # игрок находится в мульткрю
    if  is_SRV == True: return ("SOS отключен, пока вы в СРВ") #эта команда прервет выполнение, если
                                                               #игрок находится в СРВ (Если ЕДМС
                                                               #передаст эту инфу)
    if is_Fighter == True: return ("SOS отключен, пока вы в Истребителе")
    if DistFromStarLS is not None: Distance = str(",\n" + str(DistFromStarLS) + " Св.Сек.")
    else:   Distance = str("")
    
    debug(body)
    if body is not None:Body = str(",\nу " + body)
    else: Body = ""

    LifeSupport = state["Modules"]['LifeSupport']['Item']
    if   (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]]: color = 16776960
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.9 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 1.0: color = 16770560
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.8 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.9: color = 16764160
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.7 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.8: color = 16757760
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.6 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.7: color = 16751360    
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.5 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.6: color = 16744960    
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.4 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.5: color = 16738560    
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.3 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.4: color = 16732672    
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.2 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.3: color = 16725760    
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.1 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.2: color = 16719360    
    elif (fuel["FuelMain"] + fuel["FuelReservoir"]) > FuelReserwours[state["ShipType"]] * 0.0 and (fuel["FuelMain"] + fuel["FuelReservoir"]) < FuelReserwours[state["ShipType"]] * 0.1: color = 16712960
    
    
    if (fuel["FuelMain"] + fuel["FuelReservoir"]) != 0:
        if fuel_cons != 0 :
            sec_to_go = round((fuel["FuelMain"] + fuel["FuelReservoir"]) / fuel_cons ,3)
        
            time_to_go = datetime.timedelta(seconds=sec_to_go)

            params.update({"Etitle":"SOS",
                        "EDesc":str("Требуется заправка"),
                        "EColor":color,
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        "Foouter":"Расчетное время отключения:"  ,
                        "Timestamp":(time_to_go),
                        "Embed?":True,
                        "Fields":{
                            str("Местоположение:"):str(system + Distance + Body),
                            str("Топлива осталось:"):str(str(round(fuel["FuelMain"] + fuel["FuelReservoir"],2)) + " тонн"),
                            str("Времени до отключения:"):str((time_to_go)),
                            }})
        else:
            params.update({"Etitle":"SOS",
                        "EDesc":str("Требуется заправка"),
                        "EColor":color,
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        
                        "Embed?":True,
                        "Fields":{
                            str("Местоположение:"):str(system + Distance + Body),
                            str("Топлива осталось:"):str(str(round(fuel["FuelMain"] + fuel["FuelReservoir"],2)) + " тонн"),
                            str("Времени до отключения:"):str("Не кончится"),
                            }})
    else: params.update({"Etitle":"SOS",
                        "EDesc":str("Срочно требуется топливо, произведено отключение всех систем!!!"),
                        "EColor":"16711680",
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        "Foouter":str("Расчетное время смерти:"),
                        "Timestamp":(time_to_go),
                        "Embed?":True,
                        "Fields":{
                            str("Местоположение:"):str(system + Distance + Body),
                            str("Топлива осталось:"):str(str(round(fuel["FuelMain"] + fuel["FuelReservoir"],2)) + " тонн"),
                            str("Кислород кончится через (прим.):"):LifeSupportList[LifeSupport],
                            }})
    Discord.Sender(cmdr,"FuelAlarm",params)
    return "Сигнал о помощи послан, ожидайте помощь"
          


def commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,fuel,fuel_cons,is_SRV,is_Fighter):
    if entry['event'] == "SendText":
        if entry['Message'].lower() == '/sos':
            return sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons,is_SRV,is_Fighter)   