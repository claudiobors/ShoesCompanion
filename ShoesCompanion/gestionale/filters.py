import django_filters
from django import forms
from .models import Cliente, Modello, Componente, Colore, Ordine, Taglia, TipoComponente

class ClienteFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome Cliente')

    class Meta:
        model = Cliente
        fields = ['nome', 'partita_IVA']

class ModelloFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome Modello')
    cliente = django_filters.ModelChoiceFilter(
        queryset=Cliente.objects.all(),
        label='Cliente',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Modello
        fields = ['nome', 'cliente', 'tipo']

class OrdineFilter(django_filters.FilterSet):
    data_ordine = django_filters.DateFromToRangeFilter(
        label='Data Ordine (da/a)',
        widget=django_filters.widgets.RangeWidget(attrs={'type': 'date', 'class': 'form-control'})
    )
    modello__cliente = django_filters.ModelChoiceFilter(
        field_name='modello__cliente',
        queryset=Cliente.objects.all(),
        label='Cliente'
    )

    class Meta:
        model = Ordine
        fields = ['modello__cliente', 'modello', 'stato', 'data_ordine']

class ColoreFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome Colore')

    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex']

# SOSTITUISCE CoppiaMisuraFilter
class TagliaFilter(django_filters.FilterSet):
    numero = django_filters.NumberFilter(lookup_expr='exact', label='Numero Taglia Esatto')

    class Meta:
        model = Taglia
        fields = ['numero']

# AGGIORNATO ComponenteFilter
class ComponenteFilter(django_filters.FilterSet):
    nome_componente = django_filters.ModelChoiceFilter(
        field_name='nome_componente',
        queryset=TipoComponente.objects.all(),
        label='Tipo Componente'
    )
    modello = django_filters.ModelChoiceFilter(
        queryset=Modello.objects.all(),
        label='Modello'
    )

    class Meta:
        model = Componente
        fields = ['nome_componente', 'modello', 'colore']

# NUOVO FILTRO
class TipoComponenteFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome Tipo Componente')

    class Meta:
        model = TipoComponente
        fields = ['nome']