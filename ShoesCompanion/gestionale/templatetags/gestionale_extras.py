from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Filtro personalizzato per ottenere un valore da un dizionario
    usando una chiave variabile nel template.
    Uso: {{ mio_dizionario|get_item:mia_chiave }}
    """
    return dictionary.get(key)