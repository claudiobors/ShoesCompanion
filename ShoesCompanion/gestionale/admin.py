from django.contrib import admin
from .models import (
    Cliente,
    Colore,
    Modello,
    TipoComponente,
    Componente,
    Taglia,
    Articolo,
    Ordine,
    DettaglioOrdine
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'numero_telefono', 'partita_IVA', 'created_at')
    search_fields = ('nome', 'partita_IVA')
    list_filter = ('created_at',)

@admin.register(Colore)
class ColoreAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valore_hex')
    search_fields = ('nome', 'valore_hex')

@admin.register(TipoComponente)
class TipoComponenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione')
    search_fields = ('nome',)

@admin.register(Taglia)
class TagliaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'note')
    search_fields = ('numero',)
    ordering = ('numero',)

class ArticoloInline(admin.TabularInline):
    model = Articolo
    extra = 1
    autocomplete_fields = ['taglia']
    fields = ('taglia', 'descrizione_misura')

@admin.register(Componente)
class ComponenteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'modello', 'colore')
    search_fields = ('nome_componente__nome', 'modello__nome', 'modello__cliente__nome')
    list_filter = ('modello__cliente', 'modello', 'colore', 'nome_componente')
    autocomplete_fields = ('modello', 'nome_componente', 'colore')
    inlines = [ArticoloInline]

class ComponenteInline(admin.TabularInline):
    model = Componente
    extra = 1
    autocomplete_fields = ('nome_componente', 'colore')

@admin.register(Modello)
class ModelloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'tipo', 'created_at')
    search_fields = ('nome', 'cliente__nome')
    list_filter = ('tipo', 'cliente')
    inlines = [ComponenteInline]
    autocomplete_fields = ('cliente',)

class DettaglioOrdineInline(admin.TabularInline):
    model = DettaglioOrdine
    extra = 1
    autocomplete_fields = ['taglia']
    fields = ('taglia', 'quantita', 'note')

@admin.register(Ordine)
class OrdineAdmin(admin.ModelAdmin):
    list_display = ('id', 'modello', 'data_ordine', 'stato', 'quantita_totale')
    list_filter = ('stato', 'data_ordine', 'modello__cliente')
    search_fields = ('id', 'modello__nome', 'modello__cliente__nome')
    inlines = [DettaglioOrdineInline]
    autocomplete_fields = ('modello', 'created_by')
    date_hierarchy = 'data_ordine'
    ordering = ('-data_ordine',)

# Non è necessario registrare DettaglioOrdine o Articolo separatamente
# se li gestiamo solo come inline, ma può essere utile per il debug.
# admin.site.register(DettaglioOrdine)
# admin.site.register(Articolo)