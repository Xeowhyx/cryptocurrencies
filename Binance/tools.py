import datetime
import dateparser

#@INPUT: Le temps renvoyé par Binance
#@OUTPUT: Le temps dans un format reconnu par la base de donné (YYYY-MM-DDTHH-MM-SSZ)
def binance_dateparser(time):
    return str(datetime.datetime.fromtimestamp(time/1000).strftime('%Y-%m-%dT%H:%M:%SZ'))

#@INPUT : Deux tableaux, le 1er sur une crypto monnaie en euro et le deuxieme sur la meme crypto monnaie en dollar
#@OUTPUT : Un tableau correspondant aux données utiles pour la bdd
#          (TIME | VALUE_EUR | VALUE_USD | LOW_EUR | LOW_USD | HIGH_EUR | HIGH_USD | VOLUME)
def binance_dataparser(data_eur,data_us):
    time = binance_dateparser(data_us[0])
    return [time, data_eur[1], data_us[1], data_eur[3], data_us[3], data_eur[2], data_us[2], data_us[5]]

#@INPUT: Un tableau contenant les données d'un crypto en dollar
#OUTPUT: Un tableau correspondant aux données utiles à la bdd
def binance_dataparser_us(data_us):
    time = binance_dateparser(data_us[0])
    return [time, "", data_us[1], "", data_us[3], "", data_us[2], data_us[5]]

                         
                         
                         