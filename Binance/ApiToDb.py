from influxdb import InfluxDBClient
from binance.client import Client
from binance.exceptions import BinanceAPIException
import datetime
import keys
import tools

#Classe qui permet la creation du dictionnaire/Json correpondant aux données à entrer
#et gère l'envoie de ces données à la base de donnée 
class ApiTodb:

    #variables utiles à nos fonctions
    cryptos = {
                    "bitcoin":"BTC",
                    "ethereum":"ETH",
                    "ripple":"XRP",
                    "bitcoin_cash":"BCH",
                    "tether":"USDT",
                    "litecoin":"LTC",
                    "eos":"EOS",
                    "binance_coin":"BNB",
                    "cardano":"ADA"
                }

    indexs = ["bitcoin","ethereum","ripple","bitcoin_cash", "tether","litecoin","eos","binance_coin","cardano"]

    client = None 
    json_body = [] # json qui contiendra toutes les données de toutes les lignes qu'on lui donnera

    def __init__(self, host, port, db):
        self.client = InfluxDBClient(host=host, port=port) #Connexion à InfluxDB 
        self.client.switch_database(db) #Choix de la base de donnée que l'on veut utiliser (Binance|Alpha_vantage|Gecko)

    #@INPUT: Toutes les données correspondantes à une ligne de la base de 
    #Ajoute les donées dans un json afin de les envoyer plus tard
    def append(self, time="", measurement="", eur="", usd="", low_eur="", low_usd="", high_eur="", high_usd="", volume="", taux_h="",  taux_j="",  taux_s=""):
        self.json_body.append(
            {
                "time": time,
                "measurement": measurement,
        
                "fields": {
                    "eur":eur,
                    "usd": usd,
                    "low_eur": low_eur,
                    "low_usd": low_usd,
                    "high_eur": high_eur,
                    "high_usd": high_usd,
                    "volume": volume, 
                    "var_h":taux_h,
                    "var_j":taux_j,
                    "var_s":taux_s
                }
            }
        )

    #Envoie du json sur la base donnée
    #Chaque élément du json correspond a une ligne dans la bdd
    def send(self):
        self.client.write_points(self.json_body)
        self.json_body=[]#reset du json 

    #@INPUT: la date de debut et de fin de l'historique que l'on veut récuperer 
    #        avec l'interval entre chaque valeur récupere     
    #Chaque item envoyé par binance est traiter et rajouté au json tel que le model de la bdd le demande 
    #   (TIME | VALUE_EUR | VALUE_USD | LOW_EUR | LOW_USD | HIGH_EUR | HIGH_USD | VOLUME)
    def binanceToJson(self,date_debut, date_fin, interval):
        clientBinance = Client(keys.public_key, keys.secret_key)
        candles_eu=[]
        candles_us=[]
        for index in self.indexs:
            symbol = self.cryptos.get(index)
            try:
                non_error = 0
                candles_us=clientBinance.get_historical_klines(symbol=symbol+'USDT', interval=interval, start_str=date_debut, end_str=date_fin)
                print(len(candles_us))
                non_error = 1
                #candles_eu=clientBinance.get_historical_klines(symbol=symbol+'EUR', interval=interval, start_str=date_debut, end_str=date_fin)
                #non_error = 2
            except BinanceAPIException as e:
                print( str(e) + ' ' + symbol)
            finally:
                if(non_error==1 or len(candles_eu)==0):
                    for i in range(0, len(candles_us)):
                        line = tools.binance_dataparser_us(candles_us[i])
                        self.append(line[0], index, line[1], line[2], line[3], line[4], line[5], line[6], line[7])
                elif(non_error==2):
                    print(symbol + str(len(candles_us))+' '+str(len(candles_eu)))
                    for i in range(0, len(candles_us)):
                        line = tools.binance_dataparser(candles_eu[i], candles_us[i])
                        self.append(line[0], index, line[1], line[2], line[3], line[4], line[5], line[6], line[7])

    #Fonction qui va être appelé chaque minute pour récuperer les données de binance toutes les minutes
    #Chaque item envoyé par binance est traiter et rajouté au json tel que le model de la bdd le demande 
    #   (TIME | VALUE_EUR | VALUE_USD | LOW_EUR | LOW_USD | HIGH_EUR | HIGH_USD | VOLUME)
    def binanceToJsonMinute(self):
        clientBinance = Client(keys.public_key, keys.secret_key)
        candles_eu=[]
        candles_us=[]
        for index in self.indexs:
            symbol = self.cryptos.get(index)
            try:
                non_error = 0
                candles_us = clientBinance.get_klines(symbol=symbol+'USDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=2)
                print(len(candles_us))
                non_error = 1
                #candles_eu=clientBinance.get_klines(symbol=symbol+'EUR', interval=Client.KLINE_INTERVAL_1MINUTE, limit=2)
                #non_error = 2
            except BinanceAPIException as e:
                print(str(e) + ' ' + symbol)
            finally:
                if(non_error==1 or len(candles_eu)==0):
                    for i in range(0, len(candles_us)):
                        line = tools.binance_dataparser_us(candles_us[i])
                        taux = self.getRate(crypto=index, value=line[2], time=candles_us[i][0]/1000)
                        self.append(time=line[0], measurement=index, eur=line[1], usd=line[2], low_eur=line[3], low_usd=line[4], high_eur=line[5], high_usd=line[6], volume=line[7], taux_h=taux[0], taux_j=taux[1], taux_s=taux[2])
                elif(non_error==2):
                    print(symbol + str(len(candles_us))+' '+str(len(candles_eu)))
                    for i in range(0, len(candles_us)):
                        line = tools.binance_dataparser(candles_eu[i], candles_us[i])
                        taux = self.getRate(crypto=index, value=line[2], time=candles_us[i][0]/1000)
                        self.append(time=line[0], measurement=index, eur=line[1], usd=line[2], low_eur=line[3], low_usd=line[4], high_eur=line[5], high_usd=line[6], volume=line[7], taux_h=taux[0], taux_j=taux[1], taux_s=taux[2])

    #@INPUT: crypto sur laquelle le calcule va etre fait
    #        valeur actuelle récuperer de l'API
    #        le timestamp actuelle de la donné 
    #@OUTPUT: tableau contenant les taux (TAUX_HEURE | TAUX_JOUR | TAUX_SEMAINE)
    #Fonction qui va calculer le taux d'evolution d'une crypto deonné en param (heure, jour, semaine)
    def getRate(self, crypto, value, time):
        delta_h = 3600 #Nombre de seconde dans une heure pour calculer le taux dans l'heure
        delta_j = 86400 #Nombre de seconde dans un jour pour calculer le taux dans la journée
        delta_s = 604800 #Nombre de seconde dans une semaine pour calculer le taux dans la 

        #on met le un format de temps reconnaissable par la bdd
        h = datetime.datetime.fromtimestamp(time-delta_h).strftime('%Y-%m-%dT%H:%M:%SZ')
        j = datetime.datetime.fromtimestamp(time-delta_j).strftime('%Y-%m-%dT%H:%M:%SZ')
        s = datetime.datetime.fromtimestamp(time-delta_s).strftime('%Y-%m-%dT%H:%M:%SZ')

        #On récupere les données ulterieur de la bdd pour calculer le taux 
        value_h = float(list(self.client.query("select usd from " + crypto + " where time = '" + h + "'"))[0][0].get('usd'))
        value_j = float(list(self.client.query("select usd from " + crypto + " where time = '" + j + "'"))[0][0].get('usd'))
        value_s = float(list(self.client.query("select usd from " + crypto + " where time = '" + s + "'"))[0][0].get('usd'))



        #on calcule le taux pour chaque intervalle
        taux_h = ((float(value)-value_h)/float(value))*100
        taux_j = ((float(value)-value_j)/float(value))*100
        taux_s = ((float(value)-value_s)/float(value))*100

        return [taux_h, taux_j, taux_s]