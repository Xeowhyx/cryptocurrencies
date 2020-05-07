from binance.client import Client
import ApiToDb

#on récupère la derniere minute actuelle afin de mettre a jour notre BDD Influx
data = ApiToDb.ApiTodb(host='localhost', port=8086, db='binance')
data.binanceToJsonMinute()
data.send()
