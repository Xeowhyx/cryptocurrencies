#tout modele doit heriter de "Model" inclus dans
from django.db import models

from django.utils import timezone
from django.contrib.auth.models import User


# Create your models here.


#champ dans bdd
#id se mets 

#Model des actifs dans la base de donné
class Actif(models.Model):
    user = models.ForeignKey('Profile', on_delete=models.CASCADE, verbose_name="Utilisateur lié à l'actif.")
    timestamp = models.CharField(max_length=100,verbose_name="Date d'achat de la cryptomonnaie")
    monnaie = models.CharField(max_length=20,verbose_name="Nom de la cryptomonnaie achetée")
    api = models.CharField(max_length=20,verbose_name="Source selon laquelle la valeur de la cryptomonnaie sera calculée")
    quantite = models.FloatField(verbose_name="Quantité de cryptomonnaie achetée")

    #objects = models.Manager()

    class Meta:
        verbose_name="porte_monnaie"
    
    def __str__(self):
        return str(self.monnaie) + " " + str(self.quantite) 


#extension user de 1 a 1
#requette intermediaire optimisable par la suite
class Profile(models.Model):
    #user = models.OneToOneField(User,on_delete=models.CASCADE, default=None)
    user = models.OneToOneField(User,on_delete=models.CASCADE, unique=True, related_name="profile", verbose_name="Utilisateur lié au profile.")
    username=models.CharField(max_length=10, verbose_name="Nom d'utilisateur du détenteur du compte, elle sert à la connexion au compte utilisateur.")
    email=models.EmailField(max_length=254, verbose_name="Email qui sert à joindre l'utilisateur pour divers opération.")
    password=models.CharField(max_length=20, verbose_name="Mot de passe du compte utilisateur.")
    date=models.DateTimeField(default=timezone.now, verbose_name="Date de création de compte.")
    balance=models.FloatField(default=0.0, verbose_name="Balance en dollar du portefeuille d'actif, initialisé à zero. Elle évolue avec les opérations que fait l'utilisateur sur son portefeuille.")

    signup_confirmation = models.BooleanField(default=False)

    

    #meta donnee pour plus de precision bdd admin
    class Meta:
        verbose_name="nom utilisateur"
        ordering=['date']


    def __str__(self):
        #return self.user.username
        return self.username + " "  + str(self.balance)
