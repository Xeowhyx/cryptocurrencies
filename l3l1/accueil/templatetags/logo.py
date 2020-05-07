from django import template

register = template.Library()

#filtre pour faire correspondre une cryptomonnaie à son sigle
#@INPUT: value:  le nom d'une cryptomonnaie
#@OUTPUT: le sigle d'une crypto.

@register.filter
def logo(value):
    """
        Filtre permettant d'associer une monnaie à son diminutif

    **Entree**

    ``value``
        String, correspond au nom de la monnaie

    **Sortie**
    
    ```cryptos[value]``
        String, correspond au diminutif de la monnaie

    """
    cryptos = {"Bitcoin":"BTC", "Ethereum":"ETH", "Ripple":"XRP", "Bitcoin_Cash":"BCH", "Bitcoin_SV":"BSV", "Tether":"USDT", "Litecoin":"LTC", "Eos":"EOS", "Binance_Coin":"BNB", "Cardano":"ADA"}
    return cryptos[value]