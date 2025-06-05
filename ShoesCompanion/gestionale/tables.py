import django_tables2 as tables
from .models import Cliente, Modello, Componente, Colore, CoppiaMisura, Ordine


class ClienteTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/clienti/cliente_actions.html', # Assicurati che esista questo template
        orderable=False
    )

    class Meta:
        model = Cliente
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'numero_telefono', 'partita_IVA', 'created_at')


class ModelloTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/modelli/modello_actions.html', # Assicurati che esista
        orderable=False
    )

    class Meta:
        model = Modello
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome', 'cliente', 'tipo', 'created_at')


class ComponenteTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/componenti/componente_actions.html', # Assicurati che esista
        orderable=False
    )
    # 'nome' è ora 'nome_componente' (ForeignKey a TipoComponente)
    # Mostriamo il nome del TipoComponente
    nome_componente = tables.Column(accessor='nome_componente.nome', verbose_name='Tipo Componente')
    misure_associate = tables.TemplateColumn(
        template_code="""
            {% for misura_comp in record.misure_associate.all %}
                <span class="badge bg-info text-dark">{{ misura_comp.coppia_misura.descrizione_misura }}</span>
            {% empty %}
                Nessuna misura specifica
            {% endfor %}
        """,
        verbose_name="Misure Specifiche",
        orderable=False
    )


    class Meta:
        model = Componente
        template_name = "django_tables2/bootstrap4.html"
        fields = ('nome_componente', 'modello', 'colore', 'misure_associate', 'azioni') # 'azioni' aggiunto alla fine
        sequence = ('nome_componente', 'modello', 'colore', 'misure_associate', 'azioni')


class ColoreTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/colori/colore_actions.html',
        orderable=False
    )
    # Rinominato per evitare conflitto con il campo 'colore' del modello, sebbene qui sia ok.
    anteprima_colore = tables.TemplateColumn(
        template_code='<span class="badge" style="background-color: {{ record.valore_hex }}; color: {% if record.valore_hex == "#FFFFFF" or record.valore_hex == "#ffffff" %}black{% else %}white{% endif %}; border: 1px solid #ccc;">{{ record.nome }}</span>',
        verbose_name="Colore"
    )

    class Meta:
        model = Colore
        template_name = "django_tables2/bootstrap4.html"
        fields = ('anteprima_colore', 'valore_hex', 'descrizione', 'azioni')
        sequence = ('anteprima_colore', 'valore_hex', 'descrizione', 'azioni')


class CoppiaMisuraTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/coppiemisure/coppiamisura_actions.html',
        orderable=False
    )

    class Meta:
        model = CoppiaMisura
        # Aggiornato per il nuovo modello CoppiaMisura
        template_name = "django_tables2/bootstrap4.html"
        fields = ('descrizione_misura', 'numero_scarpa_riferimento', 'note', 'azioni')
        sequence = ('descrizione_misura', 'numero_scarpa_riferimento', 'note', 'azioni')


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
        fields = ('id', 'modello', 'data_ordine', 'stato', 'quantita_totale', 'azioni')
        sequence = ('id', 'modello', 'data_ordine', 'stato', 'quantita_totale', 'azioni')