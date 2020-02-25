#coding=utf-8
'''
Этот модуль предназначен для отправки состояния корабля во время выполнения стыковочных процедур для возможности координации движения больших групп кораблей
'''
import requests
from .debug import debug, error
import sys
import time
import functools
import plug
'''
    Добавление галки участия в ивенте
'''
def plugin_prefs:
    
    this.AllowSTCSbutton = tk.IntVar(value=config.getint("AllowSTCS"))
    this.AllowSTCSbutton = this.STCSButton.get()
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)
    
    nb.Checkbutton(frame, text="Включить Space Traffic Control System?", variable=this.AllowSTCSbutton).grid(row = 7, column = 0,sticky="NW")

    return frame
'''
    Перенос переменных через journal_entry
    Так же нужна переменная ShipNamе, вдальнейшем она будет задействована. В модуле ее нет.
'''
class STCS_FINAL:
    def journal_entry(self, cmdr, system, station, entry, event, body):
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.entry = entry.copy()
        self.client = client
        self.eventAltName = entry.get("Name")
        if entry.get("bodyName"):
            self.body = entry.get("BodyName")
        else:
            self.body = body

'''
    Проверка пинадлежности к class SpaceTrafficController и создане переменной по нему
    parSTCst - Parameter Space Traffic Controller start это первоначальная проверка на диспетчера
'''
           def pilot_data(parSTCfn, parPilot, parSTCst):
                if (isinstance (self.cmdr, SpaceTrafficController())=='True'):
                    parSTCst = 1
'''
    Проверка участия пилотов и диспетчера
    parSTCfn - Parameter Space Traffic Controller finish это конечная проверка на диспетчера
    parPilot - Parameter Pilot это проверка на пилота под контролем диспетчера
    Операции print указывают, что пилоты должны быть уведомлены, кем они являются в ивенте, а как это селать в плагине я не знаю.
'''
                if (parSTC == 1 and this.AllowSTCSbutton == 'True' and station == "Crown Prospect" and event == "Docked"):
                    parSTCfn = 1
                    plug.show_error("Диспетчер готов")
                if (parSTC == 0 and this.AllowSTCSbutton == 'True'):
                    parPilot = 0
                    plug.show_error("Пилот готов")
'''
    Информирование диспетчера о корабле у станции.
'''  
                if (parSTC == 0 and system == "Kagutsuchi" and body == "Crown Prospect" and event == "SupercruiseExit"):
                    print("Корабль ", ShipName, " у станции")
                    debug(pilot_data, journal_entry)
                    plug.show_error("Диспетчер! Корабль прибыл к станции.")
'''
    В процессе
''' 
