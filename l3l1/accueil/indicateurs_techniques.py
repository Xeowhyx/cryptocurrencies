from influxdb import InfluxDBClient


localhost='localhost'
jour="100"

#Fonction qui renvoie les données de la base de donnée pour le graphe principal
#@INPUT: db: La base de donnée dont on veut recuperer les datas (binance, alpha_vantage, gecko)
#        zoom: Le zoom sur lequel le graphe va être construit peut etre j, s, tm, sm, a, t (jour, semaine, un mois, six mois, annee, toujours)
#        crypto: la crypto concerné dans le graphe (bitcoin, etherum ... )
#        devise: la devise concerné dans le graphe (usd, eur)
#@OUTPUT: data_dic: un dictionnaire contenant les données correspondate au zoom a mettre dans le graphe
def get_main_data(db, zoom, crypto, devise):

    #connexion à la bdd correspondante
    client = InfluxDBClient(host=localhost,port=8086,database=db)
    data_dic = {
        "date": [],
        "usd": []
    }

    #securite au cas ou un appel est fait pour eur sur binance          
    #si la base de données est binance alors la devise ne peut etre que usd
    #du fait est que l API binance ne donne plus que des données usd
    if db == "binance":
        devise = "usd"

    #On recupere les donnees en fonction du zoom
    if zoom == 'j':
        #dans un jour il y a 1440 minutes
        #group by time(1m) veut dire que l on veut que les données soit espacés d'une minute
        data = client.query("select first("+devise+") from " + crypto + " group by time(1m) order by time desc limit 1440")
    elif zoom == 's':
        #dans une semaine il y 10080 minutes
        data = client.query("select first("+devise+") from " + crypto + " group by time(1m) order by time desc limit 10080")
    elif zoom == 'um':
        #dans un mois il y a 30 
        #1d pour des données espacés d'un jour
        data = client.query("select first("+devise+") from " + crypto + " group by time(1d) order by time desc limit 30")
    elif zoom == 'sm':
        #dans six mois il y a 180 jours 
        data = client.query("select first("+devise+") from " + crypto + " group by time(1d) order by time desc limit 180")  
    elif zoom == 'a':
        data = client.query("select first("+devise+") from " + crypto + " group by time(1d) order by time desc limit 365")
    elif zoom == 't':
        #on ne met pas de limite ici ca on veut toutes les données espacé de 1 jours
        data = client.query("select first("+devise+") from " + crypto + " group by time(1d) order by time desc")
    
    #transformation de ResultQuery renvoyé par la base de donnée en list 
    #la liste devient une double liste du type [[......]] c'est pourquoi on recupere l'index 0
    data_list = list(data)[0] 

    #Les graphe prennent des listes representant une et une seul donnée 
    #par exemple pour l axe des x il faut lui donner une liste contenant toutes les données de cette axe
    #donc on separe ce que nous renvoie la bdd en plusieurs listes que l'on met dans un data_dic pour simplifier
    #leur utilisation plus tard
    for dic in data_list:
        data_dic.get("date").append(dic.get("time"))
        if dic.get("first")!=None:
            data_dic.get("usd").append(float(dic.get("first"))) 
        else:
            data_dic.get("usd").append(dic.get("first"))#la query renvoie des champs se nommant "first_nomDeVorteColone" sauf quand il y a une colone
                                                     #en l'occurence "usd" alors le champ se nomme juste "first"

    data_dic.get('date').reverse()
    data_dic.get('usd').reverse()
    return data_dic

#Fonction qui renvoie les données concernant les indicateurs techniques pour le graphe des indicateurs techniques
#@INPUT: ind: L'indicateur technique concerné dans le graphe (ADX MACD OBV PP RSI SMA BB)
#        crypto: la crypto concerné dans le graphe
#@OUTPUT: data_dic: un dictionnaire contenant les données correspondate à l indicateur pour la crypto demandée
def get_ind_data(ind, crypto):
    
    client = InfluxDBClient(host=localhost,port=8086,database='alpha_vantage')
    data_dic = {
        "date": [],
        ind: []
    }   
    
    #ici BB ou CANLDE sont juste des codes pour savori que l'on veut les bande de Boilinger ou les Candles Stick
    # Or il n existe pas de champ BB ou CANDLE dans la BDD donc on le stransforme par autre chose 
    # tant que ca nous permet de recuperer les bonnes dates 
    if ind == "BB":
        ind = "usd"
    elif ind == "CANDLE":
        #ind == "eur"
        ind = "eur"

    #Les indicateurs techniques sont toujours presentés sur un mois avec un intervalle de 1 jour (1d) chacun
    data = client.query("select first("+ind+") from " + crypto + " group by time(1d) order by time desc limit "+jour)

    if ind == "usd":
        ind = "BB" #On le retablie a BB pour le reste du code
    elif ind == "eur":
        ind = "CANDLE"#On le retablie a CANDLE pour le reste du code
    #transformation du ResultQuery de la bdd en list
    data_list = list(data)[0]

    #meme proceder que la fonction get_main_data
    #Sauf qu'on recupere seulement la date car le reste depend de quel indicateur on veut les données
    for dic in data_list:
            data_dic.get("date").append(dic.get("time"))

    #Pour les indicateurs MACD et Bandes de Boilinger (BB) il y a plusieurs champs à recuperer
    if ind == "MACD" or ind == "BB" or ind == "PP" or ind == 'CANDLE':
        #on recupere tous les champs et en extrait que ce qu'on veut, ici le time est toujours nul c'est pourquoi nous avons fait un premier appel sans tout prendre (c'est le fonctionnement interne d Influx)
        data = client.query("select first(*) from " + crypto + " group by time(1d) order by time desc limit "+jour)
        data_list = list(data)[0]
        data_dic.pop(ind)#supression du champ ind car il devient inutile est sera remplacer par les differents champs de la bdd
        sous_dic = {} #On instancie le sous dictionnaire qui contiendra les differents champs pour MACD ou BB
        if ind == "MACD":
            #on instancie le sous dictionnaire qui contiendra les donnés pour MACD
            sous_dic = {
                "MACD":[],
                "MACD_Hist":[],
                "MACD_Signal":[]
            }

            #on ajoute les bonnes données dans les bons champs
            for dic in data_list:
                sous_dic.get("MACD").append(dic.get("first_MACD"))
                sous_dic.get("MACD_Hist").append(dic.get("first_MACD_Hist"))
                sous_dic.get("MACD_Signal").append(dic.get("first_MACD_Signal"))

        elif ind == "BB":
            #ici c est le sous dictionnaire pour les bandes de boilinger
            sous_dic = {
                "Real Middle Band":[],
                "Real Lower Band":[],
                "Real Upper Band":[]
            }

            #ON ajoute les bonnes données dans les bons champs
            for dic in data_list:
                
                if dic.get("first_Real Middle Band") is None:
                    sous_dic.get("Real Middle Band").append((dic.get("first_Real Middle Band")))
                else:
                    sous_dic.get("Real Middle Band").append(float(dic.get("first_Real Middle Band")))


                if dic.get("first_Real Lower Band") is None:
                    sous_dic.get("Real Lower Band").append((dic.get("first_Real Lower Band")))
                else:
                    sous_dic.get("Real Lower Band").append(float(dic.get("first_Real Lower Band")))
                

                if dic.get("first_Real Upper Band") is None:
                    sous_dic.get("Real Upper Band").append((dic.get("first_Real Upper Band")))
                else:
                    sous_dic.get("Real Upper Band").append(float(dic.get("first_Real Upper Band")))
                

        elif ind == "PP":        
            #ici c est le sous dictionnaire pour points de pivots
            sous_dic = {
                "PP":[],
                "S1":[],
                "S2":[],
                "S3":[],
                "R1":[],
                "R2":[],
                "R3":[]
            }

            #ON ajoute les bonnes données dans les bons champs
            for dic in data_list:
                sous_dic.get("PP").append(dic.get("first_PP"))
                sous_dic.get("S1").append(dic.get("first_S1"))
                sous_dic.get("S2").append(dic.get("first_S2"))
                sous_dic.get("S3").append(dic.get("first_S3"))
                sous_dic.get("R1").append(dic.get("first_R1"))
                sous_dic.get("R2").append(dic.get("first_R2"))
                sous_dic.get("R3").append(dic.get("first_R3"))

        else:#C'est donc forcement les chandeliers (candlestick) ind == CANDLE
            sous_dic = {
            "High":[],
            "Low":[],
            "Open":[],
            "Close":[]
            }

            #ON ajoute les bonnes données dans les bons champs

            #heu normalement y a pas de None, binance est capabe de tout recuperer
            for dic in data_list:

                if dic.get("first_high_usd"):
                    sous_dic.get("High").append(float(dic.get("first_high_usd")))
                    sous_dic.get("Low").append(float(dic.get("first_low_usd")))
                    sous_dic.get("Open").append(float(dic.get("first_open_usd")))
                    sous_dic.get("Close").append(float(dic.get("first_usd")))
                else:
                    sous_dic.get("High").append(dic.get("first_high_usd"))
                    sous_dic.get("Low").append(dic.get("first_low_usd"))
                    sous_dic.get("Open").append(dic.get("first_open_usd"))
                    sous_dic.get("Close").append(dic.get("first_usd"))
           
        #on ajoute le sous dictionnaire au dictionnaire qui sera retourné par la fonction
        data_dic.update(sous_dic)   
    else:    
        #ici on peut juste recuper le champ qui nous interesse avec la bonne date
        for dic in data_list:
            data_dic.get(ind).append(dic.get("first"))

    return data_dic
