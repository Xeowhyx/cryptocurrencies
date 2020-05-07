from binance.client import Client
from influxdb import InfluxDBClient
from datetime import date
import ApiToDb


localhost='localhost'
data = ApiToDb.ApiTodb(host=localhost, port=8086, db='binance')

#On récupère toutes les données de Binance de puis le 1 janvier 2017 jusqu'a il ya une semaine (avec un intervalle d'un jour par donnée)
data.binanceToJson(date_debut='1 Jan, 2017', date_fin='27 Apr, 2020', interval=Client.KLINE_INTERVAL_1DAY)
data.send()

#Pour chaque jour de la semaine qu'il reste à récuperer on fait une requete à Binance et le stock dans la BDD Influx  (avec un intervalle d'une minute par donnée)
for i in range(7):
    data.binanceToJson(date_debut=str(21+i)+'Apr, 2020', date_fin=str(21+i+1)+'Apr, 2020', interval=Client.KLINE_INTERVAL_1MINUTE)
    data.send()
  

#Le nombre de donnée par requete est limité donc on redemande les données de la derniere journée pour être sur qu'on a bien tout
data.binanceToJson(date_debut='28 Apr, 2020', date_fin='29 Apr, 2020', interval=Client.KLINE_INTERVAL_1MINUTE)
data.send()

client = InfluxDBClient(host=localhost,port=8086,database='binance')

dataBDD = [
{"measurement":"bitcoin_sv",
"time": str(date.today())+"T00:00:00Z",
"fields": {"a":" "}                                                        #il faut au moins un field dans la table
}
]

client.write_points(dataBDD)
