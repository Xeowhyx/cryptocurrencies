from django import template

register = template.Library()

#filtre pour afficher les noms des bases de données plus proprement
#@INPUT: value: une chaine de caractères.
#@OUTPUT : la chaine où "_" est remplacé par un espace.

@register.filter
def replace_(value):
    """
        Filtre permettant de remplacer "_" en " "

    **Entree**

    ``value``
        String

    **Sortie**

    ``value``
        String
    """
    return value.replace("_"," ")