import django_filters
from .models import Cliente, Modello, Componente, Colore, CoppiaMisura, Ordine


class ClienteFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Cliente
        fields = ['nome', 'partita_IVA']


class ModelloFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')
    cliente = django_filters.ModelChoiceFilter(queryset=Cliente.objects.all())

    class Meta:
        model = Modello
        fields = ['nome', 'cliente', 'tipo']


class ComponenteFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')
    modello = django_filters.ModelChoiceFilter(queryset=Modello.objects.all())

    class Meta:
        model = Componente
        fields = ['nome', 'modello', 'colore']


class ColoreFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex']


class CoppiaMisuraFilter(django_filters.FilterSet):
    numero_scarpa = django_filters.NumberFilter()

    class Meta:
        model = CoppiaMisura
        fields = ['numero_scarpa']


class OrdineFilter(django_filters.FilterSet):
    modello = django_filters.ModelChoiceFilter(queryset=Modello.objects.all())
    data_ordine = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Ordine
        fields = ['modello', 'stato', 'data_ordine']