from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import F
from compte.tokens import account_activation_token
from compte.forms import SignUpForm
from compte.models import Profile, Actif
from influxdb import InfluxDBClient

localhost = '90.92.107.107'
#localhost = 'localhost'

def portefeuille_view(request):
    """
        Affiche la page de porte monnaie du site

    **Entree**

    ``request``
        la requete de l'utilisateur

    **Sortie**

    ``balance``
        float, la balance de l'utilisateur

    ``actifs_tab``
        liste de dictionnaire, avec dictionnaire de taille 7 qui contient les 7 colonnes du tableau à afficher
        
    ``redirect('login')``
        redirige l'utilisateur vers la page de connection

    ``template``
        :template:`compte/portefeuille.html`
    
    """
    #Verifie si l'utilisatuer est connecté
    if request.user.is_authenticated:
        #si l'attibut vendre est dans la requete POST alors on supprime l'actif du porte monnaie
        if request.POST.get('vendre'):
            #On récupere l'actif que l'on veut vendre
            actif = Actif.objects.get(id=request.POST['vendre'])
            print(actif)
            #connexion au client Influx
            client = InfluxDBClient(host=localhost, port=8086, database=actif.api)
            #on recupere les valerus de la crypto pour po_uvoir mettre a jour la balance
            crypto_value = float(list(client.query("select usd from " + actif.monnaie + " where time='" + actif.timestamp + "'"))[0][0].get('usd')) #valeur de la crypto lors de l'achat
            crypto_now = float(list(client.query("select last(usd) from " + actif.monnaie))[0][0].get('last')) #valeur de la crypto maintenant (pour calculer l'evolution)
            #calcule d el'evolution de l'actif depuis son aachat
            evolution = (crypto_now - crypto_value)
            #On met a jour la balance du portefeuille de l'utilisateur
            Profile.objects.filter(username = request.user.username).update(balance=F('balance') + evolution + actif.quantite)
            #on supprime maintenant l'actif vendu
            actif.delete()
        #si l'attribut devise ou crypto est donné alors il faut achter la crypto avec les devises
        if request.POST.get('devise'):
            #on recupere chaque valeur qui nous interresse dans la requete
            crypto = request.POST['cryptoToUse'].lower()
            api = request.POST['api'].lower()
            quantite = request.POST['devise']
            #connexion au client Influx
            client = InfluxDBClient(host=localhost, port=8086, database=api)
            #requete pour recuperer la derniere valeur dispo pour cette crypto
            data = client.query("select last(usd) from "+crypto)
            #transformation de la requete en list pour faciliter sa manipulation
            data_list = list(data)
            #on met a jour la balance du portefeuille de l'utilisateur
            Profile.objects.filter(username = request.user.username).update(balance=F('balance') - float(quantite))
            #creation de l'actif pour le profile
            Actif.objects.create(user=request.user.profile, timestamp=data_list[0][0].get('time'), monnaie=crypto, api=api, quantite=float(quantite))

        client = InfluxDBClient(host=localhost, port=8086)
        #On récupère tous les actifs qui on en createur l'utilisateur actuel
        actifs = Actif.objects.filter(user = request.user.profile)
        actifs_tab = []
        #Pour chaque actif on fait un dictionnaire que l'on met dans un tableau que l'on passe au template 
        for actif in actifs:
            client.switch_database(actif.api)
            #Seul le timestamp est stocjer dans la bdd des utilisateurs
            #Il faut donc récuperer sur inlfux la valeur de la monnaie sur le bon timestamp
            #ne pas oublier de les transformer en flaot car ce sont des strings dans la bdd
            crypto_value = float(list(client.query("select usd from " + actif.monnaie + " where time='" + actif.timestamp + "'"))[0][0].get('usd')) #valeur de la crypto lors de l'achat
            crypto_now = float(list(client.query("select last(usd) from " + actif.monnaie))[0][0].get('last')) #valeur de la crypto maintenant (pour calculer l'evolution)
            #on calcule la valeur de l'actif lors de son achat
            value = actif.quantite / crypto_value
            date = actif.timestamp
            #calcule d el'evolution de l'actif depuis son aachat
            evolution = (crypto_now - crypto_value)
            #ajout de tous les champs dans item afin des les envoyer au template plus tard
            item = {'Nom': actif.monnaie,'Api':actif.api, 'Dollars': actif.quantite, 'Valeur': value, 'Date': date.replace('T', ' ').replace('Z', ''), 'Evolution': actif.quantite*evolution, 'id': actif.id}
            #ajout de item dans les actifs dispo pour le profil
            actifs_tab.append(item)

        return render(request, 'compte/portefeuille.html', {
            'balance': request.user.profile.balance,
            'actifs_tab':actifs_tab,
        })
    else:#Si non renvoie vers la page de connexion car le portefeuille n'est pas accessible si on est pas connecté
        return redirect('login')



def activate(request, uidb64, token):
    """
        Permet d'activer un compte.
        Cela permet de faire passer un compte User (non valide) à un compte User valide qui sera associé à un compte Profile

    **Entree**

    ``request``
        la request de l'utilisateur
    ``uidb64``
        String, slug id User encode en base64
    ``token``
        String, token creer en fonction du timestamp

    **Sortie**

    ``redirect('home')``
        redirige vers la page d'accueil

    ``template``
        :template:`compte/activation_invalid.html`

    """

    #permet d'activer le compte d un utilisateur, lorsqu il confirme son inscription
    
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        profile=Profile.objects.create(
            user=User.objects.get(pk=uid),
            username=user.username,
            email=user.email,
            balance=0.0
            )
        profile.save()
        user.save()
        login(request, user)
    #on dit qu un User valide devient profile, lorsqu il confirme son inscription
    #on ajoute donc un nouveau profile qui est lie a l User
        return redirect('home')
    else:
        return render(request, 'compte/activation_invalid.html')



#activationsentview
def activation_sent_view(request):
    return render(request, 'compte/activation_sent.html')
   
# View pour la création de compte
def signup(request):
    """
        Permet à l'utilisateur de s'inscrire

    **Entree**

    ``request``
        requete de l'utilisateur

    **Sortie**

    ``reponse``
        HttpResponse Json,
        possedant status 200 lorsque la request est bonne, le status 400 sinon.
        Ainsi que le msg à afficher pour l'utilisateur

    """
    #On vérifie par sécurité si on a bien une méthode post et que la requête a été faite par ajax
    if request.method == 'POST' and request.is_ajax():
        #on récupère les données envoyées en POST
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        #on met les données récupérées dans un formulaire au format attendu par la view Django.
        form = SignUpForm(request.POST)
        #Si le formulaire est valide, que la confirmation de mot de passe est correct, on va pouvoir enregistrer l'utilisateur dans la base de données 
        if form.is_valid() and password1 == password2:
            user = form.save(commit=False)
            print(User.objects.all())
            #Le compte est inactif tant que le mail n'est pas validé
            user.is_active = False   
            user.save()
            print(User.objects.all())
            
            #on envoie un lien pour permettre à l'utilisateur de confirmer son compte
            current_site = get_current_site(request)
            subject = 'Confirmez votre compte'
            message = render_to_string('compte/activation_request.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
            to_email=form.cleaned_data.get('email')
            email=EmailMessage(subject,message,to=[to_email])
            email.send()
            
            #Si tout c'est bien passé on renvoie un succès
            json_response={}
            reponse = JsonResponse(json_response,status=200)
        
        #Si le formulaire n'est pas valide, on va chercher le problème précisément pour renvoyer des messages précis sur la nature de l'erreur
        else:
            json_response = {'title':"Quelque chose s'est mal passé !",
                            'message':{}}

            if not username:
                json_response['message'].update({
                
                    'message1':"Merci d'utiliser un nom valide.",
                })
            if not password1:
                json_response['message'].update({
                    
                    'message3':"Merci d'entrer un mot de passe pour continuer.",
                })
            if not password1 == password2:
                json_response['message'].update({
                    
                    'message4':"La vérification du mot de passe a échoué veuillez recommencer.",
                })
            if not password2:
                json_response['message'].update({
                    
                    'message4':"Merci de confirmer votre mot de passe.",
                })
            if User.objects.filter(username=username) :
                json_response['message'].update({
                  'message5':"Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.",  
                })
            if User.objects.filter(email=email):
                json_response['message'].update({
                  'message6':"Ce mail est déjà pris. Veuillez en choisir un autre.",  
                })
            if len(password1) < 8 :
                json_response['message'].update({
                  'message7':"Le mot de passe doit être de 8 caractères minimum.",  
                })
            if not any(char.isdigit() for char in password1):
                json_response['message'].update({
                  'message8':"Le mot de passe doit contenir au moins un chiffre.",
                })
            else:
                json_response['message'].update({
                    'message2':"Merci d'utiliser un email valide.",
                })
            #dans ce cas on renvoie un échec avec le message à afficher dans l'erreur
            reponse = JsonResponse(json_response,status=400)

    return reponse

#View pour la connexion d'un utilisateur
def signin(request):
    """
        Permet à l'utilisateur de se connecter

    **Entree**

    ``request``
        requete de l'utilisateur 

    **Sortie**

    ``response``
        HttpResponse Json, avec status 200 si le formulaire est correcte, sinon status 400.
        Ainsi que des indications à afficher à l'utilisateur

    """
    
    #On vérifie par sécurité si on a bien une méthode post et que la requête a été faite par ajax
    if request.method=='POST' and request.is_ajax():
        #on récupère les données envoyées en POST
        username = request.POST.get('username')
        password = request.POST.get('password')

        #on essaye d'authentifier l'utilisateur
        user = authenticate(username=username,password=password)
        
        #si ça fonctionne on le connecte et on renvoie un succès
        if user:
            login(request,user)
            reponse = JsonResponse({},status=200)
        
        #sinon on renvoie un échec et un message explicatif
        else:
            json_response = {
                'title':"Quelque chose s'est mal passé !",
                'message':"Votre nom d'utilisateur et/ou mot de passe sont incorrects merci de recommencer."
                }
            
            reponse = JsonResponse(json_response,status=400)
        
    return reponse


#View pour changer de mot de passe
def changepwd(request):
    """
        Permet à l'utilisateur de changer son mot de passe

    **Entree**

    ``request``
        requete de l'utilisateur

    **Sortie**

    ``reponse``
        HttpResponse Json, avec status 200 si le mot de passe est modifié, 400 sinon.
        Contient aussi une indication à afficher à l'utilsateur

    """
    #On vérifie par sécurité si on a bien une méthode post et que la requête a été faite par ajax
    if request.method=='POST' and request.is_ajax():
        #on récupère les données envoyées en POST
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        conf_new_password = request.POST.get('conf_new_password')

        #si tous les champs sont remplis
        if old_password and new_password and conf_new_password:    
            
            #si le formulaire est valide on change le mot de passe et on renvoie un succès
            if request.user.check_password(old_password) and new_password == conf_new_password:
                request.user.set_password(new_password)
                request.user.save()
                reponse = JsonResponse({},status=200)
            
            #si c'est la confirmation du nouveau mot de passe qui a échoué on renvoie un échec avec un message explicatif
            elif not new_password == conf_new_password:
                reponse = JsonResponse({'message':'La confirmation du nouveau mot de passe a échoué veuillez recommencer'},status = 400)
            
            #si c'est la confirmation de l'ancien mot de passe qui a échoué on renvoie un échec avec un message explicatif
            else :
                reponse = JsonResponse({'message':"L'ancien mot de passe n'est pas correct, veuillez recommencer"},status = 400)      

        #si tous les champs ne sont pas remplis on renvoie un échec avec un message explicatif
        else:
            reponse = JsonResponse({'message':'Veuillez remplir tous les champs, merci'},status = 400)

    return reponse

#View qui s'occupera d'enregistrer en cookies les préférences d'un utilisateur
def preference_view(request):
    """
        Gestion des préferences cookies

    **Entree**

    ``request``
        requete de l'utilisateur

    **Sortie**   

    ``reponse``
        HttpResponse Json, avec status 200 lorsque les préferences sont enregisré, status 400 sinon

    """
    #On vérifie par sécurité si on a bien une méthode post et que la requête a été faite par ajax
    if request.method=='POST' and request.is_ajax():
        #on récupère les données du formulaire envoyé 
        pref_api = request.POST.get('pref_api')
        pref_zoom = request.POST.get('pref_zoom')
        pref_ind = request.POST.get('pref_ind')
        #initialisation de la réponse pour déclarer que tout s'est bien passé
        reponse = JsonResponse({}, status=200)

        #ajout des cookies à la réponse pour qu'ils soient sauvegardés dans les cookies du navigateur
        #domain sert à déclarer dans quel domaine les cookies sont valides
        reponse.set_cookie('pref_api', pref_api, domain=settings.SESSION_COOKIE_DOMAIN)
        reponse.set_cookie('pref_zoom', pref_zoom, domain=settings.SESSION_COOKIE_DOMAIN)
        reponse.set_cookie('pref_ind', pref_ind, domain=settings.SESSION_COOKIE_DOMAIN)
    else:
        #si nous sommes ici c'est que quelque chose s'est mal passé 
        reponse = JsonResponse({}, status=400)

    return reponse

def mail_exist(request):
    """
        verification de l'existence d'un email

    **Entree**

    ``request``
        requete de l'utilisateur

    **Sortie**  

    ``reponse``
        HttpResponse Json, avec status 200 lorsque le mail est existe déjà, status 400 sinon

    """
    #on récupère les données envoyées en POST
    email = request.POST.get('email')

    #si le mail est dans la base de données on renvoie un succès sinon un échec
    if User.objects.filter(email=email).exists():
        response = JsonResponse({},status=200)
    else:
        response = JsonResponse({},status=400)
    
    return response
