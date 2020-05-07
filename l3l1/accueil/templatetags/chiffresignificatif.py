from django import template

register = template.Library()

#filtre pour avoir 3 chiffres aprés la virgule en gardant les None et en formatant les strings
#@INPUT: value:  la valeur à arrondir
#@OUTPUT: la valeur arrondi

@register.filter
def chiffresignificatif(value):
    """
        Filtre permettant d'arrondir à 3 chiffres après la virgule les String

    **Entree**

    ``value``
        String, qui correspond à la valeur de la monnaie

    **Entree**

    ``res``
        String, qui correspond à valeur de la monnaie arrondi
    
    """
    res = value
    if (value) :
        try :
            res = round(float(res),3)
        except ValueError :
            pass
    return res