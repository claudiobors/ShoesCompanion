from django.contrib import admin
from .models import (
    Cliente, Modello, Componente, Colore,
    CoppiaMisura, Ordine, DettaglioOrdine,
    TipoComponente, MisuraComponente  # Nuovi modelli importati
)

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'numero_telefono', 'partita_IVA', 'created_at')
    search_fields = ('nome', 'partita_IVA')
    list_filter = ('created_at',)

class ModelloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'tipo', 'created_at')
    search_fields = ('nome', 'cliente__nome')
    list_filter = ('tipo', 'cliente', 'created_at')

# Inline per MisuraComponente all'interno di ComponenteAdmin
class MisuraComponenteInline(admin.TabularInline):
    model = MisuraComponente
    extra = 1 # Numero di form vuoti da mostrare
    autocomplete_fields = ['coppia_misura'] # Se hai molte CoppiaMisura

class ComponenteAdmin(admin.ModelAdmin):
    # 'nome' è stato sostituito da 'nome_componente' che è un ForeignKey a TipoComponente
    list_display = ('get_nome_componente_display', 'modello', 'colore')
    search_fields = ('nome_componente__nome', 'modello__nome') # Cerca sul nome del TipoComponente
    list_filter = ('modello', 'colore', 'nome_componente')
    autocomplete_fields = ['modello', 'nome_componente', 'colore'] # Utile per ForeignKey
    inlines = [MisuraComponenteInline]

    def get_nome_componente_display(self, obj):
        return obj.nome_componente.nome
    get_nome_componente_display.short_description = 'Tipo Componente'
    get_nome_componente_display.admin_order_field = 'nome_componente__nome'


class ColoreAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valore_hex')
    search_fields = ('nome', 'valore_hex')

class CoppiaMisuraAdmin(admin.ModelAdmin):
    # Aggiornato per il nuovo modello CoppiaMisura
    list_display = ('descrizione_misura', 'numero_scarpa_riferimento', 'note')
    search_fields = ('descrizione_misura', 'numero_scarpa_riferimento')
    list_filter = ('numero_scarpa_riferimento',)

class DettaglioOrdineInline(admin.TabularInline):
    model = DettaglioOrdine
    extra = 1
    autocomplete_fields = ['coppia_misura_scarpa']

class OrdineAdmin(admin.ModelAdmin):
    list_display = ('id', 'modello', 'data_ordine', 'stato', 'quantita_totale')
    search_fields = ('modello__nome', 'id')
    list_filter = ('stato', 'data_ordine')
    inlines = [DettaglioOrdineInline]
    autocomplete_fields = ['modello', 'created_by']

class TipoComponenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')
    search_fields = ('nome',)

admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Modello, ModelloAdmin)
admin.site.register(TipoComponente, TipoComponenteAdmin) # Registra TipoComponente
admin.site.register(Componente, ComponenteAdmin)
admin.site.register(Colore, ColoreAdmin)
admin.site.register(CoppiaMisura, CoppiaMisuraAdmin) # Già presente, ma assicurati che sia per il nuovo modello
admin.site.register(MisuraComponente) # Registra MisuraComponente (opzionale, utile per debug)
admin.site.register(Ordine, OrdineAdmin)
# DettaglioOrdine non necessita di registrazione separata se gestito solo inline.