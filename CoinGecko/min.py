from pycoingecko import CoinGeckoAPI
import json
from influxdb import InfluxDBClient


db=InfluxDBClient(host='localhost', port=8086)
db.switch_database('gecko')
#connexion gecko


cm=['bitcoin',
    'ethereum',
    'Ripple',
    'bitcoin-cash-sv',
    'bitcoin-cash',
    'Tether',
    'Litecoin',
    'Eos',
    'BinanceCoin',
    'Cardano'
]
#tableau de nom des crypto de l'api
cg=CoinGeckoAPI()


dico=cg.get_price(ids=cm, vs_currencies=['usd','eur'], include_market_cap='true', include_24hr_vol='true', include_24hr_change='true', include_last_updated_at='true')
#recupereation des donnee avec l api

def settitre(k):
    if k=='Ripple':
        k="xrp"
    elif k=='bitcoin-cash-sv':
        k='bitcoin_cash'
    elif k=='bitcoin-cash':
        k='bitcoin_sv'
    elif k=='Tether':
        k='tether'
    elif k=='Litecoin':
        k='litecoin'
    elif k=='Eos':
        k='eos'
    elif k=='binancecoin':
        k='binance_coin'
    elif k=='Cardano':
        k='cardano'
    return k
#ranme des nom des crypto

def dicoTojsonli(dico):
    json=[]
    for (k,v) in dico.items():
        json.append({
                    "time": v['last_updated_at'],
                    "measurement": settitre(k), #rename pour nom a respecter
        })
        del v['last_updated_at']
        v["var_j"] = v.pop('usd_24h_change')
        v["volume"]= v["usd_24h_vol"]
        json[-1]['fields']=v
        #manipulation des champs, pour normaliser les donnee entre les differentes base
    return json


json=dicoTojsonli(dico)
db.write_points(json,time_precision="s")
#ecriture a dans la bdd

