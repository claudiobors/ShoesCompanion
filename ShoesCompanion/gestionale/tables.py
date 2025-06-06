import django_tables2 as tables
from django_tables2.utils import A  # Per creare link dinamici
from .models import Cliente, Modello, Componente, Colore, Ordine, Taglia, TipoComponente

# --- Tabelle Principali ---

class ClienteTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/clienti/cliente_actions.html',
        orderable=False, verbose_name='Azioni'
    )
    nome = tables.LinkColumn('cliente_detail', args=[A('pk')], verbose_name="Nome Cliente / Ragione Sociale")

    class Meta:
        model = Cliente
        template_name = "django_tables2/bootstrap5.html"
        fields = ('nome', 'numero_telefono', 'partita_IVA', 'azioni')
        sequence = ('nome', 'numero_telefono', 'partita_IVA', 'azioni')

class ModelloTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/modelli/modello_actions.html',
        orderable=False, verbose_name='Azioni'
    )
    nome = tables.LinkColumn('modello_detail', args=[A('pk')])
    cliente = tables.LinkColumn('cliente_detail', args=[A('cliente.pk')])

    class Meta:
        model = Modello
        template_name = "django_tables2/bootstrap5.html"
        fields = ('nome', 'cliente', 'tipo', 'created_at', 'azioni')
        sequence = ('nome', 'cliente', 'tipo', 'created_at', 'azioni')

class OrdineTable(tables.Table):
    id = tables.LinkColumn('ordine_detail', args=[A('pk')], verbose_name="Ordine #")
    stato = tables.TemplateColumn(
        template_code='''
        <span class="badge fs-6
            {% if record.stato == 'BOZZA' %}bg-secondary
            {% elif record.stato == 'CONFERMATO' %}bg-primary
            {% elif record.stato == 'IN_PRODUZIONE' %}bg-warning text-dark
            {% elif record.stato == 'COMPLETATO' %}bg-success
            {% else %}bg-danger
            {% endif %}">
            {{ record.get_stato_display }}
        </span>
        '''
    )
    azioni = tables.TemplateColumn(
        template_name='gestionale/ordini/ordine_actions.html',
        orderable=False, verbose_name='Azioni'
    )

    class Meta:
        model = Ordine
        template_name = "django_tables2/bootstrap5.html"
        fields = ('id', 'modello', 'modello.cliente', 'data_ordine', 'stato', 'quantita_totale', 'azioni')
        sequence = ('id', 'modello', 'modello.cliente', 'data_ordine', 'stato', 'quantita_totale', 'azioni')
        # Rinomina l'intestazione della colonna per chiarezza
        verbose_names = {
            'modello.cliente': 'Cliente'
        }


# --- Tabelle per Oggetti di Configurazione ---

class ColoreTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/colori/colore_actions.html',
        orderable=False, verbose_name='Azioni'
    )
    nome = tables.TemplateColumn(
        template_code='''
        <span class="badge fs-6" style="background-color: {{ record.valore_hex }}; color: {% if record.valore_hex|lower == '#ffffff' %}black{% else %}white{% endif %}; border: 1px solid #ccc;">
            {{ record.nome }}
        </span>
        '''
    )
    class Meta:
        model = Colore
        template_name = "django_tables2/bootstrap5.html"
        fields = ('nome', 'valore_hex', 'descrizione', 'azioni')

# NUOVA Tabella per Taglia (sostituisce CoppiaMisuraTable)
class TagliaTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/taglie/taglia_actions.html', # <-- Da creare
        orderable=False, verbose_name='Azioni'
    )
    numero = tables.LinkColumn('taglia_detail', args=[A('pk')]) # <-- Da creare URL e vista

    class Meta:
        model = Taglia
        template_name = "django_tables2/bootstrap5.html"
        fields = ('numero', 'note', 'azioni')

# NUOVA Tabella per TipoComponente
class TipoComponenteTable(tables.Table):
    azioni = tables.TemplateColumn(
        template_name='gestionale/tipicomponente/actions.html', # <-- Da creare
        orderable=False, verbose_name='Azioni'
    )
    nome = tables.LinkColumn('tipocomponente_detail', args=[A('pk')]) # <-- Da creare URL e vista

    class Meta:
        model = TipoComponente
        template_name = "django_tables2/bootstrap5.html"
        fields = ('nome', 'descrizione', 'azioni')