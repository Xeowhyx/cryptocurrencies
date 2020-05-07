# cryptocurrencies

## Vidéo présentation

https://drive.google.com/open?id=13xil6HJ-w_AECNaFHPCnBdQkxDRWYlJx \
https://drive.google.com/open?id=1rXATkv_IdEsyWNiYeLXXcs1L1Pn4-cHw

(en cour)

## Configuration

- éditer le fichier Alpha_Vantage/Alpha_vantageToDb.py
```python
key = "YOUR_KEY"
```
mettre votre clé alpha avantage, nécessaire pour recevoir des données de l'api

éditer le fichier Binance/key.py\
```python
public_key = 'YOUR_PUBLIC_KEY'
secret_key = 'YOUR_SECRET_KEY'
```
mettre votre clé binance, nécessaire pour recevoir des données de l'api

- éditer le fichier l3l1/l3l1/settings.py
```python
SECRET_KEY = 'YOUR_SECRET_KEY'
```
mettre votre clé django\
puis
```python
ADMINs = (
    ('YOUR_USER_NAME','YOUR_MAIL_ADRESS')
)
```
mettre votre compte admin, nécessaire pour accéder à la page administrateur\
puis
```
EMAIL_USE_TLS=True
EMAIL_HOST='smtp.gmail.com'
EMAIL_HOST_USER='YOUR_MAIL_ADRESS'
EMAIL_HOST_PASSWORD='YOUR_PWD'
EMAIL_PORT=587
```
mettre votre adresse mails, necessaire à la confirmation de compte lors d'inscription


## Requirements
```
pip install -r requirements.txt
```
Django 3.0.2

## Note
les scripts suivant permettent de remplir la bdd influxDB:\
Alpha_Vantage\Alpha_vantageToDb.py\
Binance\BinanceToDbMinute.py\
CoinGecko\min.py\
Exécutez les chaques minutes, avec par exemple l'outils crontab.

Pour avoir votre clé, et savoir précisement la limite des requetes des API veuillez regarder la documentation de Alpha Vantage, Binance, CoinGecko
