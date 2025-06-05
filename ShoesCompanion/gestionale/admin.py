from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Cliente, Modello, Componente, Colore, 
    CoppiaMisura, Ordine, DettaglioOrdine
)

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'numero_telefono', 'partita_IVA', 'created_at')
    search_fields = ('nome', 'partita_IVA')
    list_filter = ('created_at',)

class ModelloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'tipo', 'created_at')
    search_fields = ('nome', 'cliente__nome')
    list_filter = ('tipo', 'cliente', 'created_at')

class ComponenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modello', 'colore')
    search_fields = ('nome', 'modello__nome')
    list_filter = ('modello', 'colore')

class ColoreAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valore_hex')
    search_fields = ('nome', 'valore_hex')

class CoppiaMisuraAdmin(admin.ModelAdmin):
    list_display = ('numero_scarpa', 'larghezza', 'altezza')
    search_fields = ('numero_scarpa',)
    list_filter = ('numero_scarpa',)

class DettaglioOrdineInline(admin.TabularInline):
    model = DettaglioOrdine
    extra = 1

class OrdineAdmin(admin.ModelAdmin):
    list_display = ('id', 'modello', 'data_ordine', 'stato', 'quantita_totale')
    search_fields = ('modello__nome',)
    list_filter = ('stato', 'data_ordine')
    inlines = [DettaglioOrdineInline]

admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Modello, ModelloAdmin)
admin.site.register(Componente, ComponenteAdmin)
admin.site.register(Colore, ColoreAdmin)
admin.site.register(CoppiaMisura, CoppiaMisuraAdmin)
admin.site.register(Ordine, OrdineAdmin)