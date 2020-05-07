from . import definition
from .indicateurs_techniques import get_main_data,get_ind_data
from influxdb import InfluxDBClient

from django.shortcuts import render
import pandas as pd
from math import pi

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource,HoverTool,CrosshairTool, Band
from bokeh.layouts import column
from bokeh.models.widgets import Panel, Tabs



localhost='localhost'
jour="100"


def home (request):
    """
      Affiche la page d'accueil du site avec le tableau des statistiques générales des cryptomonnaies

      **Context**

      ``API``
          L'API choisi par l'utilisateur grace à la liste déroulante où avec ses préférences.
          Par défaut vaut CoinGecko

      ``crypto``
        Tableau contenant le nom de toutes les cryptomonnaies.

      ``tableau``
        Un Json contenant toutes les données des statistiques générales des cryptomonnaies
        prises dans la base de données de l'API "API".

      ``client``
        La connexion à la base de cdonnées contenant les informations à mettre dans le tableau.
      

      **Entree**

      ``request``
        la requete de l'utilisateur

      **Sortie**

      ``tableau``
        Dictionnaire python, qui contient la monnaie ainsi que tout les champs à afficher

      ``API``
        Le nom de l'API

        :template:`preference.html`
    """ 


    #boucle pour permettre à un utilisateur de choisir l'API depuis laquelle on prend les informations dans le tableau  
    if request.POST.get('API'):
      db = request.POST.get('API')
    elif request.COOKIES.get('pref_api'):
      db = request.COOKIES.get('pref_api')    #s'il n'y a pas de demande explicite via POST d'une api alors on met l'api de préférence
    else:
      db = "Gecko"                            #s'il n'y a pas de préférence non plus alors un choix par défaut est fait

    client = InfluxDBClient(host=localhost, port=8086,database=db.lower())

    #pour chaque cryptomonnaie on fait une requête à la base de données séléctionnée par l'utilisateur      
    cryptos = ["Bitcoin", "Ethereum", "Ripple", "Bitcoin_Cash", "Bitcoin_SV", "Tether", "Litecoin", "Eos", "Binance_Coin", "Cardano"]
    tableau = {}
    for key in cryptos:
        data = client.query('select last(*) from '+key.lower())                                 #on récupère la valeur la plus récente dans la base de données pour remplir le tableau
        data_list = list(data)
        tableau.update({key:{"capboursiere":data_list[0][0].get('last_usd_market_cap'),         #on crée un dictionnaire avec comme clé une cryptomonnaie et comme valeur les données qui seront mises dans le tableau. Si une donnée n'existe pas dans la base de données renvoie none à la place. Certaines cases du tableau seront donc remplies de none.         
                              "eur":data_list[0][0].get('last_eur'),
                              "usd": data_list[0][0].get('last_usd'),
                              "volume": data_list[0][0].get('last_volume'),
                              "taux_h": data_list[0][0].get('last_var_h'),
                              "taux_j": data_list[0][0].get('last_var_j'),
                              "taux_s": data_list[0][0].get('last_var_s')
                            }
        })
    return render(request,'accueil/tableau.html',{'tableau':tableau,"API":db})


def detail(request,id):

    """
      Affiche la page détails site contenant 2 graphiques dont un composé de plusieurs module, ainsi qu'une description
      les boutons permettents d'interagir avec le graphique 1 
      Les graphiques possèdent quelques outils, tel que zoom, sauvegarde.
    
    **Context**

    ``graphique 1``
        Contient le cours de la monnaie en cours

    ``graphique 2``
        Contient le graphique avancé composé de plusieurs graphiques secondaire interactif

    ``description``
        Une description ("definition.py") de la monnaie selectionné

    **Entrée**

    ``request``
        la requete de l'utilisateur

    ``id`` 
        String, nom de la monnaie

    **Sortie**

    ``script``
      String du code js, pour le graphique 1

    ``script2``
      String du code js, pour le graphique 2
      
    ``div``
      objet graphique 1 afficher

    ``div2``
      objet graphique 2 a afficher

    ``crypto``
      String, nom de la monnaie

    ``about``
      String, définition de la monnaie

    ``link``
      String, lien wikipedia vers la monnaie

    ``template``
      :template:`details.html`

    """



    if(request.method == "POST"):#on vérifie si une méthode post exist 
      if(request.POST.get("duree")):#si dans le post existe alors on le récupère     
        duree= request.POST.get('duree')
      if(request.POST.get("API")):    
        bd= request.POST.get('API')
    if(request.COOKIES.get('pref_api')):#s'il existe des préférences dans les cookies
      if 'duree' not in locals(): #on vérifie si la variable existe (si elle existe c'est qu'on l'a instancié avec la méthode post)
        duree = request.COOKIES.get("pref_zoom")
      if 'bd' not in locals():
        bd = request.COOKIES.get("pref_api")

    if 'duree' not in locals(): #si même après ça les variables n'existent pas alors on leur donne une valeur par défaut
      duree = "um"
    if 'bd' not in locals():
      bd = "binance"    


    #=========================================== figure 1, graphique du prix de la monnaie
  
    res=get_main_data(bd,duree,id,"usd")
    #recupere les données necessaires pour le prix de la monnaie

    hover = HoverTool()
    hover.tooltips = [
    ("prix", "@y{0,00}$"),
    ("date", "@x{%Y-%m-%d %H:%M:%S}"),
    ]

    hover.formatters={
        '@x':'datetime'
    }
    hover.mode="vline"
    
    #on creer un hover, et on lui l'ensemble des champs titre (constant) et valeur (variable) des courbes en fonction de la position hover de la souris.
    #les valeurs afficher subissent des formatage pour plus de visiblite
    
    TOOLS=['save','wheel_zoom','pan','box_zoom','reset']
    #les outils du graphique

    
    df = pd.DataFrame(res)
    df['date'] = pd.to_datetime(df['date'])

    p = figure(plot_height=600, x_axis_type="datetime", tools=TOOLS, sizing_mode="stretch_width")
    #creation d'un objet figure
    p.tools.append(hover)
    #ajout du hover a la figure
    
    p.line(df['date'], df['usd'], color='navy', alpha=0.5)
    #on ajoute une courbe de type line a notre figure
    p.circle(df['date'], df['usd'],color='red',size=2)

    if duree=="j":
      txt_duree=" de la journée"
    elif duree=="s":
      txt_duree=" de la semaine"
    elif duree=="um":
      txt_duree=" du mois"
    elif duree=="sm":
      txt_duree=" des 6 derniers mois"
    elif duree=="a":
      txt_duree=" de l'année"
    else:
      txt_duree=""

    p.title.text="cours du "+id.title()+txt_duree+" avec "+bd.replace("_"," ").title()
    #mise en forme des titres
    p.xaxis.axis_label = 'temps'
    p.yaxis.axis_label = 'prix usd'
    p.background_fill_color = "white"
    p.xaxis.major_label_orientation = pi/4
    script,div=components(p)
    #genere un objet qui sera envoye au fichier html

    
    #=========================================== figure 2 graphique principal

    res2=get_ind_data("CANDLE",id)
    #recuperation des donnees pour le graphe e chandelle
  
    df = pd.DataFrame(res2)
    df["date"] = pd.to_datetime(df["date"])

    #pour generer un graphique chandelle, clandestick, on le decompose en plusieurs figures
    #des rectangles (vert ou rouge), et des segments (en arriere plan) permettant d avoir le min/max quotidiens

    mids = (df.Open + df.Close)/2
    spans = abs(df.Close-df.Open)
    inc = df.Close > df.Open
    dec = df.Open > df.Close
    w = 12*60*60*1000
    #permet aussi de placer le rectangle dans le graphe
    #w permet d obtenir la largeur
    #inc et dec sont des panda series permettant de differencier les monte et les descende pour differencier les futur bonne couleur
    #mids nous sera utile pour avoir le milieu, necessaire pour la creation d un rectangle

    

    
    TOOLS=['save','wheel_zoom','pan','box_zoom','reset']
    #source drawn est un outils personnalise permettant de dessin a main leve
    #on l ajoute aux autre outils que nous proposons, permettant de se deplacer dans la figure, de faire des zoom ect
    
    p2 = figure(plot_height=600,x_axis_type="datetime", tools=TOOLS, sizing_mode="stretch_width")
    #creation de la deuxieme figure, qui contiendra l ensemble des courbes techniques
    cross = CrosshairTool()
    p2.add_tools(cross)
    #creation de crosshair, puis ajout a notre objet p2
   


    p2.title.text="Chandelier du "+id+" à intervalle journalier"
    p2.xaxis.major_label_orientation = pi/4
    p2.xaxis.axis_label = 'temps'
    p2.yaxis.axis_label = 'prix usd'
    p2.background_fill_color = "white"
    #initialisation des champs titres, et de propriete basique

    p2.segment(df.date, df.High, df.date, df.Low, color="black")
    #ajout de courbe segment, permettant de visualiser la valeur minimum et maximum quotidienne

    p2.rect(df.date[inc], mids[inc], w, spans[inc], fill_color="green", line_color="black")
    p2.rect(df.date[dec], mids[dec], w, spans[dec], fill_color="red", line_color="black")
    #ajout de courbe de type rectangle, permettant de visualiser la variation de l actif, entre la date d ouverture et fermeture de la journee
    #differenciation de couleur lorsqu on detecte une croissance en vert, ou une decroissance en rouge



    ################################### deuxième indicateur technique sur le graphique principal de la figure 2

    data_bb=get_ind_data("BB",id)
    #recupere les données nécessaires pour indicateur Boilinger
  
    dfbb = pd.DataFrame(data_bb)
    
 
    band_source = ColumnDataSource(data=dict(
      date=df['date'],
      lowera=dfbb['Real Middle Band'],
      uppera=dfbb['Real Lower Band'],
      middlea=dfbb['Real Upper Band']
      ))

    c_hover=HoverTool()
    c_hover.tooltips=[
      ('date', '@x{%F}'),
      ]
    c_hover.formatters={
        '@x':'datetime'
    }
    c_hover.name='lines1'
    
    maband=Band(base='date',lower='uppera', upper='middlea', fill_alpha=0.08, source=band_source, fill_color='blue')
    #creation de la courbe de type bande (glyph), les donnee necessaire a la creation sont passe par la bande_source, permettant de remplir
    #en transparant bleu, l'espace entre la courbe superieur et inferieur
    p2.line(df['date'], dfbb['Real Middle Band'], color='blue', alpha=1)
    #creation de courbe de type line, elle permet de mettre en evidence le milieu de la bande
    p2.add_layout(maband)
    #p2.add_tools(c_hover)
    


    ################################### troisième indicateur technique sur le graphique principal de la figure 2


    data_pivot=get_ind_data("PP",id)
    #récupération des données pour les points de pivot
    dfp = pd.DataFrame(data_pivot)

    source_segment = ColumnDataSource(dict(
        x=df['date'],
        pp=dfp['PP'],
        s1=dfp['S1'],
        s2=dfp['S2'],
        s3=dfp['S3'],
        r1=dfp['R1'],
        r2=dfp['R2'],
        r3=dfp['R3']
      )
    )

    #on creer une source associe a nos rectangle, permettant de faire passer tout nos donnee necesaire.
    #on recupere la meme donnee date, du clandestick, elle est commune a toutes les courbes qui sont dans la p2 ainsi qu au graphique annexe.
    #en effet elle correspond au 100 dernier jour, a frequence de 1 points par jour
    
    p2.rect(x='x', y='r3', width=2*w, height=0.0001, source=source_segment, fill_color="red", line_color="red", legend_label="r3")
    p2.rect(x='x', y='r2', width=2*w, height=0.0001, source=source_segment, fill_color="red", line_color="red", legend_label="r2")
    p2.rect(x='x', y='r1', width=2*w, height=0.0001, source=source_segment, fill_color="red", line_color="red", legend_label="r1")
    p2.rect(x='x', y='pp', width=2*w, height=0.0001, source=source_segment, fill_color="black", line_color="black", legend_label="p")
    p2.rect(x='x', y='s1', width=2*w, height=0.0001, source=source_segment, fill_color="green", line_color="green", legend_label="s1")
    p2.rect(x='x', y='s2', width=2*w, height=0.0001, source=source_segment, fill_color="green", line_color="green", legend_label="s2")
    p2.rect(x='x', y='s3', width=2*w, height=0.0001, source=source_segment, fill_color="green", line_color="green", legend_label="s3")

    #creation de 7 pivot de type rectangle, le rectangle est centré a la date x, puis deborde horizontalement de la date de "w" a gauche et a droite
    #la hauteur de 1, permet de simuler un trait.
    #le choix du rectangle (et non de Ray ou de Segment) a ete fait, car la courbe Rectangle permet de centré la figure, et que plus haut, nous avons
    #deja calculer la taille w
    #les pivots sont affiché par couleur differentes

    p2.legend.location = "top_right"
    p2.legend.click_policy="hide"

    #permet d afficher une legende a gauche, avec nos 7 pivot
    #lorsqu un utilisateur clic sur la "legend_label" de la legend, il peut "hide" la courbe, permettant une visualisation plus personnalisé et propre



    ########################################################### figure 2 graphique annexe

    #ici on s occupe des graphiques annexe de la figure2
  
    res2b=get_ind_data("MACD",id)
    #récupération des données pour le macd
    #le macd_hist = macd-macd_signal


    dfb = pd.DataFrame(res2b)  

    p2b = figure(plot_height=300, x_axis_type="datetime", tools=TOOLS, sizing_mode="stretch_width",x_range=p2.x_range, background_fill_color = "white")
    p2b.add_tools(cross)
    #création d une figure annexe avec qui est liée avec la principale
    #ils possedent la meme dimension de largeur, mais aussi le meme cross permettant de liée ses 2 graphiques
    
    macolor=[]
    for ele in dfb['MACD_Hist']:
        if ele is not None:
            if float(ele)<0:
                macolor.append('red')
            else:
                macolor.append('green')
        else:
            macolor.append('green')
    #on possede les valeurs pour le digramme histogramme (a barre), maintenant on la parcours pour verifier les valeurs
    #et les noter dans un tableau

    p2b.vbar(x=df['date'], top=dfb['MACD_Hist'], color=macolor, width=w, alpha=0.5)
    #creation du digramme a barre, avec notre code couleur predefinis plus haut, ameliore la visibilite du client
    p2b.line(df['date'], dfb['MACD'], line_width=2, color='red', legend_label="macd")
    p2b.line(df['date'], dfb['MACD_Signal'], line_width=2, color='green', legend_label="macd_Signal")
    #affichage des courbes de type line


    p2b.legend.click_policy="hide"
    p2b.legend.location = "top_right"

    

    tab1 = Panel(child=p2b, title="macd")
    #on cree un systeme d onglet dans notre graphique secondaire
    #puis on ajoute ce graphique secondaire


    ########################################################### figure 3 graphique annexe OBV
    
    client = InfluxDBClient(host=localhost,port=8086,database="alpha_vantage")
    #connexion a la bdd alpha_vantage
    res=client.query("select first(OBV) from  "+id+"  group by time(1d) order by time desc limit "+jour)
    #recuperation des donnees necessaire pour OBV (on balance volume)

    data_dic = {
        "obv": []
    }

    data_list = list(res)[0]
    for dic in data_list:
      if (dic.get("first")) != None:
        data_dic.get("obv").append(float(dic.get("first")))
      else:
        data_dic.get("obv").append(dic.get("first"))

    data_dic.get('obv').reverse()   
    dfObv = pd.DataFrame(data_dic)
    #netoyage des donnee permettant une plus simple manipluation


    p2obv = figure(plot_height=300, x_axis_type="datetime", tools=TOOLS, sizing_mode="stretch_width",x_range=p2.x_range, background_fill_color = "white")
    p2obv.add_tools(cross)
    #creation d'une figure p2obv, qui partage le meme crosshair et x_range que la figure p2, permettant d avoir des graphiques liee
    

    hover_obv = HoverTool()
    hover_obv.tooltips = [
    ("obv", "@y{0,00}"),
    ("date", "@x{%F}"),
    ]

    hover_obv.formatters={
        '@x':'datetime'
    }
    hover_obv.mode="vline"
    p2obv.tools.append(hover_obv)
    #creation du hover, puis ajout sur la figure

    p2obv.line(df['date'], dfObv['obv'], line_width=1, color='blue', legend_label="obv")
    #creation de courne de type line
    p2obv.legend.location = "top_right"

    tab2 = Panel(child=p2obv, title="obv")
    #ajout de la figure sur un deuxieme onglet

    ########################################################### figure 3 graphique annexe RSI

    res=client.query("select first(RSI) from  "+id+"  group by time(1d) order by time desc limit "+jour)
    #recuperation des donnees necessaire pour OBV (on balance volume)

    data_dic = {
        "rsi": []
    }

    data_list = list(res)[0]
    for dic in data_list:
      if (dic.get("first")) != None:
        data_dic.get("rsi").append(float(dic.get("first")))
      else:
        data_dic.get("rsi").append(dic.get("first"))

    data_dic.get('rsi').reverse()
    #netoyage des donnee permettant une plus simple manipluation
   
    dfRsi = pd.DataFrame(data_dic)
    p2rsi = figure(plot_height=300, x_axis_type="datetime", tools=TOOLS, sizing_mode="stretch_width",x_range=p2.x_range, background_fill_color = "white")
    p2rsi.add_tools(cross)
    #creation d une figure, avec liaison avec la figure principe p2
    #meme x_range, meme tools, permettant une syncrhonisation du zoom, des deplacements ect

    hover_rsi = HoverTool()
    hover_rsi.tooltips = [
    ("rsi", "@y{0,00}"),
    ("date", "@x{%F}"),
    ]

    hover_rsi.formatters={
        '@x':'datetime'
    }
    hover_rsi.mode="vline"
    p2rsi.tools.append(hover_rsi)

    p2rsi.line(df['date'], dfRsi['rsi'], line_width=1, color='blue', legend_label="rsi")
    #ajout de courbe de type line

    bandcst=Band(base='date',lower=30, upper=70, fill_alpha=0.08, source=band_source, fill_color='blue')
    p2rsi.add_layout(bandcst)
    #ajout d une bande, entre 30 et 70, car ce sont des valeurs remarquable utilise dans l analyse du rsi
    #il est donc pertinent d ajouter cet indicateur
    p2rsi.legend.location = "top_right"

    tab3=Panel(child=p2rsi, title="rsi")
    tabs=Tabs(tabs=[tab1,tab2,tab3])
    #ajout de la derniere figure en tant qu'onglet
    script2,div2=components(column(p2,tabs))
    #rendu en colonne, de la figure p2 et des graphiques secondaire represente en forme d onglet

    return render(request,'accueil/detail.html',{
        'script':script,
        'script2':script2,
        'div':div,
        'div2':div2,
        'crypto':id,
        'about':definition.definition[id],
        'link': definition.lien[id],
        })
    #render vers la page html, avec les arguments necesasires pour l affichage
