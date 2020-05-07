from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from . import models

# Create your tests here.
class PortefeuilleTests(TestCase):
    
    def setUp(self):
        #on crée un compte et on active le compte test qui viens d'être crée
        user = User.objects.create_user('testuser', 'test@test.com', 'testpasswd')
        user.is_active = True
        profile=models.Profile.objects.create(
            user=user,
            username=user.username,
            email=user.email,
            balance=0.0
            )
        profile.save()
        user.save()
        self.client.force_login(user)

    #On test si la page portefeuille charge bien. 
    def test_affiche_portefeuille(self):

        reponse_test_affiche_portefeuille = self.client.get(reverse('portefeuille'))
        
        self.assertEqual(reponse_test_affiche_portefeuille.status_code, 200)
        #On vérifie que la view charge bien le template
        self.assertTemplateUsed(reponse_test_affiche_portefeuille, 'compte/portefeuille.html')

    #On test si l'achat se fait bien.   
    def test_achat(self):

        #les données à envoyer pour acheter une cryptomonnaie.
        dataAchat = {
            'api' : 'Binance',
            'cryptoToUse' : 'Bitcoin',
            'devise' : '10.0',
        }
        #On test si l'achat est réussi.
        reponse_test_achat = self.client.post(reverse('portefeuille'), dataAchat)
        self.assertEqual(reponse_test_achat.status_code, 200)

        #On test si l'achat a été écrit dans la base de données.
        self.assertTrue(models.Actif.objects.filter(monnaie='bitcoin'))

    
    #On teste si la vente se fait bien.   
    def test_vente(self):

        #il faut avoir acheter une cryptomonnaie pour la vendre.
        #les données à envoyer pour acheter une cryptomonnaie.
        dataAchat2 = {
            'api' : 'alpha_vantage',
            'cryptoToUse' : 'Bitcoin',
            'devise' : '10.0',
        }
        #On teste si l'achat est réussi.
        self.client.post(reverse('portefeuille'), dataAchat2)

        #les données à envoyer pour vendre une cryptomonnaie.
        dataVente = {
            'vendre' : 1,
        }
        #On teste si la vente est réussi.
        reponse_test_vente = self.client.post(reverse('portefeuille'), dataVente,)
        self.assertEqual(reponse_test_vente.status_code, 200)

        #On teste si la vente a été écrit dans la base de données.
        self.assertFalse(models.Actif.objects.filter(monnaie='bitcoin'))

class ModalTests(TestCase):

    def setUp(self):
        #on crée un compte et on active le compte test qui viens d'être crée
        user = User.objects.create_user('testuser', 'test@test.com', 'testpasswd')
        user.is_active = True
        user.save()

    #on teste la création de compte 
    def test_signup_success(self):

        #les données à envoyer pour créer un compte
        dataCountSuccess = {
            'username' : 'testuser2',
            'email' : 'test2@test.com',
            'password1' : 'testpasswd',
            'password2' : 'testpasswd',
        }
        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_signup = self.client.post(reverse('signup'), dataCountSuccess, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(reponse_test_signup.status_code, 200)
        #on teste si l'utilisateur soit bien écrit dans la base de données
        self.assertTrue(User.objects.filter(username='testuser'))
        #on vérifie si un mail d'activation à bien était envoyé
        self.assertEqual(mail.outbox[0].subject, 'Confirmez votre compte')
    

    def test_signup_fail(self):

        #les données à envoyer pour créer un compte
        dataCountFail = {
            'username' : 'testuser2',
            'email' : 'test2@test.com',
            'password1' : 'testpasswd',
            'password2' : 'testpasswdazerty',
        }
        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_signup = self.client.post(reverse('signup'), dataCountFail, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        #on vérifie qu'on a bien un échec
        self.assertEqual(reponse_test_signup.status_code, 400)


    def test_signin_success(self):
        #on teste la connexion au compte

        #les données à envoyer pour créer se connecter
        dataLogSuccess = {
                'username' : 'testuser',
                'password' : 'testpasswd',
        }
        user = User.objects.get(username='testuser')
        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_signin = self.client.post(reverse('signin'), dataLogSuccess, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(reponse_test_signin.status_code, 200)
        #on test si l'utilisateur est bien connecté
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_signin_fail(self):
        #on teste la connexion au compte

        #les données à envoyer pour créer se connecter
        dataLogFail = {
                'username' : 'testuser2',
                'password' : 'testpasswd',
        }

        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_signin = self.client.post(reverse('signin'), dataLogFail, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        #on vérifie qu'on a bien un échec        
        self.assertEqual(reponse_test_signin.status_code, 400)
       

    def test_changepwd_success(self):
        #on teste le changement de mot de passe

        #les données à envoyer pour changer le mot de passe
        dataChangeSuccess = {
                'old_password' : 'testpasswd',
                'new_password' : 'testpasswd_new',
                'conf_new_password' : 'testpasswd_new',
        }
        #il faut être connécté pour changer le mot de passe
        user = User.objects.get(username='testuser')
        self.client.force_login(user)
        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_changepwd = self.client.post(reverse('changepwd'), dataChangeSuccess, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(reponse_test_changepwd.status_code, 200)
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password(dataChangeSuccess['new_password']))



    
    def test_changepwd_fail(self):
        #on teste le changement de mot de passe

        #les données à envoyer pour changer le mot de passe
        dataChangeFail = {
                'old_password' : 'testpasswdfail',
                'new_password' : 'testpasswd_new',
                'conf_new_password' : 'testpasswd_new',
        }
        #il faut être connécté pour changer le mot de passe
        user = User.objects.get(username='testuser')
        self.client.force_login(user)
        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_changepwd = self.client.post(reverse('changepwd'), dataChangeFail, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(reponse_test_changepwd.status_code, 400)


    def test_resetpassword(self):
        #on teste le reset de mot de passe

        #les données à envoyer pour reset le mot de passe
        dataResetSuccess = {
                'email':'test@test.com',
        }

        #la view verifie si on envoie une requête ajax donc on rajoute **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        reponse_test_changepwd = self.client.post(reverse('password_reset'), dataResetSuccess, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.assertEqual(reponse_test_changepwd.status_code, 302)
        #on vérifie si un mail de réinitialisation à bien était envoyé
        self.assertEqual(mail.outbox[0].subject, 'Password reset on testserver')