from urllib import quote_plus
import requests
import json
from debug import Debug
from debug import debug,error

class Systems():

    '''
        Caching all the Canonn Systems because we don't want to hit them up every time 
        we start the plugin
    '''
    systemCache={
        #Системы СЕС
"Kagutsuchi":[-11.5,-84.5625,-162.65625],
"Gaezatorix":[-0.78125,-74.375,-149.15625],
"Arietis Sector EQ-Y c17":[-24.53125,-87.6875,-166.4375],
"Obamumbo":[-9.03125,-78.59375,-152.90625],
"Scythia":[6.75,-76.90625,-150.34375],
"HIP 17305":[-35.25,-72.53125,-153.9375],
"Arietis Sector DQ-Y c18":[-27.28125,-71.9375,-168.9375],
"Arietis Sector DQ-Y c16":[-28.125,-79.8125,-157.03125],
"HIP 18843":[-9.5625,-87.40625,-173.5],
"HIP 20419":[9.625,-73.0625,-153.375],
"HIP 18609":[-15.96875,-85.65625,-173.90625],
"Bhillke":[-0.59375,-83.09375,-137.21875],
"HIP 15412":[-41.0625,-100.875,-159.21875],
"HIP 20827":[4.96875,-65.65625,-158.5625],
"HIP 19757":[10.3125,-82.3125,-153.125],
#Системы ЕГП
"Euryale":[35.375,-68.96875,24.8125],
"Mamaragan":[33.875,-49.09375,26.4375],
"LHS 1379":[38.34375,-64.03125,5.125],
"Arare":[28.125,-40.5625,30.78125],
"LFT 78":[33,-58.875,21.71875],
"Chup Kamui":[26.28125,-39.15625,21.5],
"Nanabozho":[22.9375,-35.75,24.15625],
"Lauksa":[17.8125,-33.96875,60.6875],
"L 119-33":[25.1875,-43.375,34.34375],
"Putamasin":[37.21875,-76.375,21.28125],
"CPC 20 6743":[23.71875,-55.90625,54.9375],
"HDS 3215":[31.53125,-54.21875,40.78125],
"Caelinus":[0.1875,-18.625,52.0625],
"LTT 464":[22.8125,-64.96875,14.8125],
"Sanna":[35.96875,-83.3125,23.125],
"Fjorgyn":[38.375,-43.71875,42.125],
"LTT 305":[27.6875,-75.28125,21.8125],
"Aparctias":[25.1875,-56.375,22.90625],
"Veroandi":[33.15625,-37.625,32.25],
"CD-61 6651":[25.53125,-55.15625,46.4375],
"Chapsugaibo":[42.5625,-80.78125,10.0625],
"Kappa Tucanae":[39.5625,-51.0625,22.28125],
"Mat Zemlya":[37.03125,-56.5,24.71875],
"LTT 9387":[33.15625,-49.21875,33.8125],
"LTT 9181":[31.96875,-61.6875,43.03125],
"LHS 3615":[8.65625,-37.78125,42.09375],
"LHS 1020":[20.78125,-77.125,25.625],
"LTT 700":[40.78125,-52.8125,23.03125],
"Kerebaei":[50.96875,-67.875,6.9375],
"Algreit":[-8.3125,-11.78125,53.28125],
"Ullese":[35.75,-73.78125,38.96875],
"LFT 1442":[8.375,-17,41.875],
"Gebel":[23.40625,-50.90625,29.375],
"LP 91-140":[38.71875,-35.53125,9.84375],
"Rishalu":[18.625,-32.25,59.4375],
"Tiolce":[10.5,-34.78125,25.0625],
"LFT 1594":[10.78125,-27.125,29.46875],
"Clayakarma":[-20.5,-4.96875,60.6875],
"Viracocha":[14,-46.4375,9.65625],
    }

    @classmethod
    def edsmGetSystem(cls,system):
        
        if cls.systemCache.has_key(system):
        
            return cls.systemCache[system]
            
        else:
            url = 'https://www.edsm.net/api-v1/system?systemName='+quote_plus(system)+'&showCoordinates=1'      
            r = requests.get(url)
            s =  r.json()
        
            cls.systemCache[system]=(s["coords"]["x"],s["coords"]["y"],s["coords"]["z"])
            return s["coords"]["x"],s["coords"]["y"],s["coords"]["z"]    
            
    @classmethod      
    def dump(cls):
        for x in cls.systemCache.keys():
            debug('"{}":[{},{},{}],'.format(x, cls.systemCache.get(x)[0],cls.systemCache.get(x)[1],cls.systemCache.get(x)[2]))

def edsmGetSystem(system):
    Systems.edsmGetSystem(system)
    
def dumpSystemCache():
    Systems.dump()