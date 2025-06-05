import django_filters
from .models import Cliente, Modello, Componente, Colore, CoppiaMisura, Ordine, TipoComponente


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
    # 'nome' è ora 'nome_componente' (ForeignKey a TipoComponente)
    # Filtriamo per il nome del TipoComponente
    nome_componente = django_filters.ModelChoiceFilter(
        field_name='nome_componente',
        queryset=TipoComponente.objects.all(),
        label='Tipo Componente'
    )
    # Oppure, se vuoi filtrare per il testo del nome del TipoComponente:
    # nome_componente_text = django_filters.CharFilter(field_name='nome_componente__nome', lookup_expr='icontains', label='Nome Tipo Componente')

    modello = django_filters.ModelChoiceFilter(queryset=Modello.objects.all())
    colore = django_filters.ModelChoiceFilter(queryset=Colore.objects.all())


    class Meta:
        model = Componente
        fields = ['nome_componente', 'modello', 'colore']


class ColoreFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex']


class CoppiaMisuraFilter(django_filters.FilterSet):
    # Aggiornato per il nuovo modello CoppiaMisura
    descrizione_misura = django_filters.CharFilter(lookup_expr='icontains')
    numero_scarpa_riferimento = django_filters.NumberFilter()

    class Meta:
        model = CoppiaMisura
        fields = ['descrizione_misura', 'numero_scarpa_riferimento']


class OrdineFilter(django_filters.FilterSet):
    modello = django_filters.ModelChoiceFilter(queryset=Modello.objects.all())
    data_ordine = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Ordine
        fields = ['modello', 'stato', 'data_ordine']