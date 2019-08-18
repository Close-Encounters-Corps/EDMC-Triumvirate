
# -*- coding: utf-8 -*-
import Discord
import load
import datetime
from debug import debug

import l10n
import functools
_ = functools.partial(l10n.Translations.translate, context=__file__)  

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
    
    if state['Role'] != None: return "You're in the crew, SOS signal is disabled" # Вы находитесь в экипаже, SOS отключено (Эта команда прервет выполнение, если игрок находится в мульткрю)    
    if  is_SRV == True: return ("SOS signal is disabled while you are in SRV") # SOS отключен, пока вы в СРВ (эта команда прервет выполнение, если игрок находится в СРВ (Если ЕДМС передаст эту инфу))
    if is_Fighter == True: return ("SOS signal is disabled while you are in fighter")  # SOS отключен, пока вы в истребителе
    if DistFromStarLS is not None: Distance = unicode(u",\n" + unicode(DistFromStarLS) + u" Св.Сек.")
    else:   Distance = unicode("")
    
    debug(body)
    if body is not None:Body = unicode(u",\nу " + body)
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
            sec_to_go = (fuel["FuelMain"] + fuel["FuelReservoir"]) / fuel_cons
        
            time_to_go = datetime.timedelta(seconds=sec_to_go)

            params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Refueling required"), # Требуется дозаправка
                        "EColor":color,
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        "Foouter":"Estimated time before shutdown:", # Рассчетное время до отключения
                        "Timestamp":(time_to_go),
                        "params":{
                            unicode(u"Location:"):unicode(system + Distance + Body), # Местоположение
                            unicode(u"Fuel left:"):unicode(str(fuel["FuelMain"] + fuel["FuelReservoir"]) + u" tons"), # Топлива осталось # тонн
                            unicode(u"Estimated time before shutdown:"):unicode(time_to_go), # Рассчетное время до отключения
                            }})
        else:
            params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Refueling required"), # Требуется дозаправка
                        "EColor":color,
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        
                        
                        "params":{
                            unicode(u"Location:"):unicode(system + Distance + Body), # Местоположение
                            unicode(u"Fuel left:"):unicode(str(fuel["FuelMain"] + fuel["FuelReservoir"]) + u" tons"), # Топлива осталось # тонн
                            unicode(u"Estimated time before shutdown:"):unicode(u"Won't end"), # Рассчетное время до отключения # Не кончится
                            }})
    else: params.update({"Etitle":"SOS",
                        "EDesc":unicode(u"Urgent refueling is required, all systems are disconnected!"), # Требуется срочная дозаправка, произведено отключение всех систем!
                        "EColor":"16711680",
                        "Avatar":"https://raw.githubusercontent.com/VAKazakov/EDMC-Triumvirate/master/.github/FuelAlarmIcon.png",
                        "Foouter":unicode("Estimated time to destruction:"), # Расчетное время до уничтожения
                        "Timestamp":(time_to_go),
                        "params":{
                            unicode(u"Location:"):unicode(system + Distance + Body), # Местоположение
                            unicode(u"Fuel left:"):unicode(str(fuel["FuelMain"] + fuel["FuelReservoir"]) + u" tons"), # Топлива осталось # тонн
                            unicode(u"Oxygen will end in (approx.):"):LifeSupportList[LifeSupport], # Кислород кончится через (прим.)
                            }})
    Discord.Sender(cmdr,"FuelAlarm",params)
    return "Help signal transmitted, please wait" # Сигнал о помощи передан, пожалуйста ожидайте
          


def commands(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client,fuel,fuel_cons,is_SRV,is_Fighter):
    if entry['event'] == "SendText":
        if entry['Message'].lower() == '/sos':
            return sos(cmdr,system,DistFromStarLS,state,body,lat,lon,fuel,fuel_cons,is_SRV,is_Fighter)   