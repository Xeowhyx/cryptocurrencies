from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized



class AccueilTests(TestCase):
    
    #On teste si la page d'accueil charge bien avec tous les templates.
    @parameterized.expand(['accueil/tableau.html','base.html', 'signup.html', 'signin.html', 'preference.html', 'change_password.html', 'password_reset.html', 'signup.js.html', 'signin.js.html', 'change_password.js.html', 'preference.js.html', 'password_reset.js.html'])    
    def test_affiche_accueil(self,templates):


        reponse_test_affiche_accueil = self.client.get(reverse('home'))
        
        self.assertEqual(reponse_test_affiche_accueil.status_code, 200)
        self.assertTemplateUsed(reponse_test_affiche_accueil, templates)
    
    #Pour chaque Api, on regarde si on envoie bien des données pour remplir le tableau
    @parameterized.expand(['Gecko','Binance','Alpha_Vantage'])
    def test_affiche_tableau(self,api):

        dataApi = {
            'API':api
        }

        reponse_test_affiche_tableau = self.client.post(reverse('home'),dataApi)
        self.assertTrue(reponse_test_affiche_tableau.context['tableau'])

class DétailsTests(TestCase):
    
    #On teste si la page détail charge bien avec toutes les cryptomonnaies.
    @parameterized.expand(['bitcoin', 'ethereum', 'ripple', 'bitcoin_cash','litecoin', 'eos', 'binance_coin', 'cardano'])    
    def test_affiche_detail(self,crypto):


        reponse_test_affiche_detail = self.client.get(reverse('detail',kwargs={'id':crypto}))
        
        self.assertEqual(reponse_test_affiche_detail.status_code, 200)
        #On vérifie que la view charge bien le template
        self.assertTemplateUsed(reponse_test_affiche_detail, 'accueil/detail.html')
