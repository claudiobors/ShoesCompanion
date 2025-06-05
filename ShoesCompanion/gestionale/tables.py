import django_tables2 as tables
from .models import Cliente, Modello, Componente, Colore, CoppiaMisura, Ordine


class ClienteTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/clienti/cliente_actions.html',
        orderable=False
    )

    class Meta:
        model = Cliente
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'numero_telefono', 'partita_IVA', 'created_at')


class ModelloTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/modelli/modello_actions.html',
        orderable=False
    )

    class Meta:
        model = Modello
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'cliente', 'tipo', 'created_at')


class ComponenteTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/componenti/componente_actions.html',
        orderable=False
    )

    class Meta:
        model = Componente
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'modello', 'colore')


class ColoreTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/colori/colore_actions.html',
        orderable=False
    )
    colore = tables.TemplateColumn(
        template_code='<span class="badge" style="background-color: {{ record.valore_hex }}; color: {% if record.valore_hex == "#FFFFFF" %}black{% else %}white{% endif %}">{{ record.nome }}</span>'
    )

    class Meta:
        model = Colore
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'valore_hex')


class CoppiaMisuraTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/coppiemisure/coppiamisura_actions.html',
        orderable=False
    )

    class Meta:
        model = CoppiaMisura
        template_name = "django_tables2/bootstrap4.html"
        fields = ('numero_scarpa', 'larghezza', 'altezza')


class OrdineTable(tables.Table):
    stato = tables.TemplateColumn(
        template_code='<span class="badge {% if record.stato == "BOZZA" %}bg-secondary{% elif record.stato == "CONFERMATO" %}bg-primary{% elif record.stato == "IN_PRODUZIONE" %}bg-warning text-dark{% elif record.stato == "COMPLETATO" %}bg-success{% else %}bg-danger{% endif %}">{{ record.get_stato_display }}</span>'
    )
    azioni = tables.TemplateColumn(
        template_name='gestionale/ordini/ordine_actions.html',
        orderable=False
    )

    class Meta:
        model = Ordine
        template_name = "django_tables2/bootstrap4.html"
        fields = ('id', 'modello', 'data_ordine', 'stato', 'quantita_totale')