#!/usr/bin/env python3

import json
import datetime
import requests
import time
from datetime import date, datetime, timedelta
from influxdb import InfluxDBClient
from pexpect import expect

# Début du décompte de temps
start_time = time.time()

key="YOUR_KEY"	
	#symbole des cryptomonnaies dont on veut les données

cryptos = {"BTC":"bitcoin","ETH":"ethereum","XRP":"ripple","BCH":"bitcoin_cash","USDT":"tether","LTC":"litecoin","EOS":"eos","BNB":"binance_coin","ADA":"cardano"}	#fait correspondre un symbole au nom de sa cryptomonnaie, le nom complet sera utilisée comme "measurement" dans la base de donnée

client = InfluxDBClient(host='localhost',port=8086,database='alpha_vantage')		#connexion à influxdb en local utilisation de alpha vantage

API_URL = "https://www.alphavantage.co/query"

#@INPUT:key = clé utilisée pour accéder à l'API,symbol = identifiant d'une cryptomonnaie
#@OUTPUT une liste contenant toutes les données d'une cryptomonnaie   
def dataDict(key,symbol):
	
	#crée une requête pour recupérer les données de l'API sur une cryptomonnaie sur les 5 minutes en USD
	dataRequeteMinUSD = {"function": "TIME_SERIES_INTRADAY",
    "symbol" :symbol+"USD",
    "interval":"5min",
    "outputsize":"full",
    "apikey" : key}
	
	#crée une requête pour recupérer les données de l'API sur une cryptomonnaie sur les 5 minutes en EUR
	dataRequeteMinEUR = {"function": "TIME_SERIES_INTRADAY",
    "symbol" :symbol+"EUR",
    "interval":"5min",
    "outputsize":"full",
    "apikey" : key}
	
	#crée une requête pour recupérer les données de l'API sur une cryptomonnaie sur la journée	
	dataRequete = { "function": "DIGITAL_CURRENCY_DAILY",
	"symbol" : symbol,
	"market" : "EUR",		#marché sur lequel on souhaite obtenir les données
	"apikey" : key}

	#récupère les réponses des requêtes au dessus au format json 
	#l'API limite à 5 requêtes par minute d'où le sleep de 12 secondes
	try:
		reponse_json = requests.get(API_URL, dataRequete).json()['Time Series (Digital Currency Daily)']
		time.sleep(13)
		reponse_success = True
	except KeyError:
		reponse_json = {datetime.today().strftime("%Y-%m-%d"):{'a':0}}
		reponse_success = False
	#On fait un try sur la réponse car suivant l'heure de la journée la requête peut renvoyer une erreur.
	try:
		reponse_jsonMinUSD = requests.get(API_URL, dataRequeteMinUSD).json()['Time Series (5min)']
		time.sleep(12)
	except KeyError:
		reponse_jsonMinUSD = {}
	try:
		reponse_jsonMinEUR = requests.get(API_URL, dataRequeteMinEUR).json()['Time Series (5min)']
		time.sleep(12)
	except KeyError:
		reponse_jsonMinEUR = {datetime.today().strftime("%Y-%m-%d %H:%M:%S"):{'a':0}}

	dataCrypto=[]			#liste qui va contenir les données reçues après la requête à l'API, les données sont formatées selon les champs que l'on veut avoir dans la base de données

	#on passe les données récupérées au format désiré pour la base de données pour chaque date dans le json
	
	for date in reponse_json:
		
		#pour calculer l'indicateur technique du point pivot il faut la date de la veille
		dateVeille = datetime.strptime(date,"%Y-%m-%d")-timedelta(1)
		try:
			highVeille = float(reponse_json[str(dateVeille).split()[0]]['2b. high (USD)'])
			lowVeille = float(reponse_json[str(dateVeille).split()[0]]['3b. low (USD)'])
			closeVeille = float(reponse_json[str(dateVeille).split()[0]]['4b. close (USD)'])
		except KeyError:
			highVeille = 0
			lowVeille = 0
			closeVeille = 0
		#Pour calculer la variation sur les 7 derniers jours il faut récupérer la valeur d'ouverture 7 jours avant pour chaque date
		dateDebSemaine = datetime.strptime(date,"%Y-%m-%d")-timedelta(7)
		try :
			j_open=float(reponse_json[date]['1b. open (USD)'])
			j_close=float(reponse_json[date]['4b. close (USD)'])
		except KeyError : 
			j_open = 1
			j_close = 1
		pointPivot=pointP(highVeille,lowVeille,closeVeille)
		#pour les 7 dates les plus anciennes on ne peut pas calculer la variation sur les 7 derniers jours
		try:
			s_open=float(reponse_json[str(dateDebSemaine).split()[0]]['1b. open (USD)'])
			s_close=float(reponse_json[date]['4b. close (USD)'])
		except KeyError:
			s_open=1
			s_close=1
		try :
			dataCrypto.append({"measurement":cryptos[symbol],
				"time":date+"T00:00:00Z",
				"fields":{
					"eur":reponse_json[date]['4a. close (EUR)'],
					"usd":reponse_json[date]['4b. close (USD)'],
					"open_eur":reponse_json[date]['1a. open (EUR)'],
					"open_usd":reponse_json[date]['1b. open (USD)'],
					"low_eur":reponse_json[date]['3a. low (EUR)'],
					"low_usd":reponse_json[date]['3b. low (USD)'],
					"high_eur":reponse_json[date]['2a. high (EUR)'],
					"high_usd":reponse_json[date]['2b. high (USD)'],
					"var_j":((j_close-j_open)/j_open)*100,
					"var_s":((s_close-s_open)/s_open)*100,
					"volume":reponse_json[date]['5. volume']}
			})
		except KeyError :
			dataCrypto.append({"measurement":cryptos[symbol],
				"time":date+"T00:00:00Z",
				"fields":{"a":" "}
			})
		dataCrypto[-1]["fields"].update(pointPivot)
		
		#on rajoute à la liste les données aux 5 minutes
		#la boucle peut avoir des erreurs Keyerror, on passe à l'itération suivante
		for dateMinEUR in reponse_jsonMinUSD:
			try:
				if dateMinEUR.startswith(date):
					#Pour calculer la variation sur l'heure il faut récupérer la valeur d'ouverture 1 heure avant pour chaque date
					dateDebHeur = datetime.strptime(dateMinEUR,"%Y-%m-%d %H:%M:%S")-timedelta(0,3600) 
					#pour les données les plus anciennes on ne peut pas calculer la variation sur l'heure
					try:
						h_open=float(reponse_jsonMinUSD[str(dateDebHeur)]['1. open'])
						h_close=float(reponse_jsonMinUSD[dateMinEUR]['4. close'])
					except KeyError:
						h_open=1
						h_close=1
					
					dataCrypto.append({"measurement":cryptos[symbol],
					"time":dateMinEUR.split()[0]+"T"+dateMinEUR.split()[1]+"Z",
					"fields":{
					"eur":reponse_jsonMinEUR[dateMinEUR]['4. close'],
					"usd":reponse_jsonMinUSD[dateMinEUR]['4. close'],
					"low_eur":reponse_jsonMinEUR[dateMinEUR]['3. low'],
				 	"low_usd":reponse_jsonMinUSD[dateMinEUR]['3. low'],
					"high_eur":reponse_jsonMinEUR[dateMinEUR]['2. high'],
					"high_usd":reponse_jsonMinUSD[dateMinEUR]['2. high'],
					"var_h":((h_close-h_open)/h_open)*100,
					"var_j":((j_close-j_open)/j_open)*100,
					"var_s":((s_close-s_open)/s_open)*100,
					"volume":reponse_jsonMinUSD[dateMinEUR]['5. volume']
					}
					})
			except KeyError:
				print(dateMinEUR)	
			
			
	
	return dataCrypto


#@INPUT:key = clé utilisée pour accéder à l'API,symbol = identifiant d'une cryptomonnaie
#@OUTPUT:une liste contenant toutes les données des indicateurs techniques d'une cryptomonnaie 
def indtoDict(key,symbol):
	indicateurs=["MACD","RSI","ADX","BBANDS","OBV"] 			#liste des indicateurs techniques
	
	#crée une requête pour recupérer les données de l'API sur les indicateurs technniques d'une cryptomonnaie sur la journée
	dataRequete = { "function": "SMA",
		"symbol" : symbol+"USD",
		"interval" : "daily",
		"time_period":"20",
		"series_type":"open",
		"apikey" : key}
 
 	#on remplit un dictionnaire avec les données d'un indicateur technique pour pouvoir update le dictionnaire par rapport aux dates qui sont clés dans le dictionnaire
	dictIndicateurs = requests.get(API_URL, dataRequete).json()['Technical Analysis: SMA']
	time.sleep(12)
	formatDateIndicateur(dictIndicateurs)
	
	#boucle pour récupérer les informations des indicateurs techniques
	for ind in indicateurs:
		dataRequete = { "function": ind,
		"symbol" : symbol+"USD",
		"interval" : "daily",
		"time_period":"20",
		"series_type":"open",
		"apikey" : key}
		
		#récupère les réponses des requêtes au dessus au format json 
		#l'API limite à 5 requêtes par minute d'où le sleep de 12 secondes
		reponseInd = requests.get(API_URL, dataRequete).json()['Technical Analysis: '+ind]
		time.sleep(12)
		formatDateIndicateur(reponseInd)
		
		#on fusionne les dictionnaires récupérés
		for date in reponseInd:
			try:
				dictIndicateurs[date].update(reponseInd[date])
			except KeyError:
				print(ind)
	
	return dictIndicateurs	
	
#pour les indicateurs techniques l'API peut renvoyer la date du jour en y-m-d ou en y-m-d H:M:S
#@INPUT: un dictionnaire avec la date mal formatée
#@OUTPUT: le dictionnaire avec les dates formatées
def formatDateIndicateur(dictionnaire):
	for date in dictionnaire:
		if date.startswith(datetime.today().strftime("%Y-%m-%d")):
			#rajoute les données au bon format
			dictionnaire.update({datetime.today().strftime("%Y-%m-%d"): dictionnaire[date]})
			#supprime les données au mauvais format
			del dictionnaire[date]
			break


#Fonction de calcul des Points Pivots    
#@INPUT: highVeille: le cours le plus haut de la veille
#        lowVeille: le cours le plus bas de la veille
#        close: le cours de clôture
#@OUTPUT: un dictionnaire contenant le pivot les 3 supports Sk et les 3 résistances Rk
def pointP (highVeille, lowVeille, close):
    pivot = (highVeille + lowVeille + close) / 3
    res={"PP":pivot,
         "S1":(2 * pivot) - highVeille,
         "S2":pivot-(highVeille - lowVeille),
         "S3":lowVeille - 2 * (highVeille - pivot),
         "R1":(2 * pivot) - lowVeille,
         "R2":pivot + (highVeille - lowVeille),
         "R3":highVeille + 2 * (pivot - lowVeille)
         }
    return res


#boucle qui pour chaque cryptomonnaie récupère ses données et ses indicateurs techniques et qui les fusionne pour l'envoyer à la base de données
for symbol in cryptos:
	print(cryptos[symbol])
	dataCryptos = dataDict(key, symbol)
	indCryptos = indtoDict(key, symbol)
	for measure in dataCryptos:
		try:
			measure["fields"].update(indCryptos[measure["time"].split("T")[0]])
		except KeyError:
			pass
	client.write_points(dataCryptos)



#bitcoin_Sv n'est pas dans l'API on l'ajoute avec des valeurs vides dans la base de données

dataBDD = [
{"measurement":"bitcoin_sv",
"time": str(date.today())+"T00:00:00Z",
"fields": {"a":" "}                                                        #il faut au moins un field dans la table
}
]

client.write_points(dataBDD)



# Affichage du temps d'éxécution
print("Temps d execution : %s secondes ---" % (time.time() - start_time))
