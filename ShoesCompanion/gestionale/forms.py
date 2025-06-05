from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Cliente, Modello, Componente, Colore,
    CoppiaMisura, Ordine, DettaglioOrdine,
    TipoComponente, MisuraComponente # Nuovi modelli
)


class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'numero_telefono', 'indirizzo', 'partita_IVA', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class ModelloForm(ModelForm):
    class Meta:
        model = Modello
        fields = ['cliente', 'nome', 'tipo', 'foto', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class TipoComponenteForm(ModelForm):
    class Meta:
        model = TipoComponente
        fields = ['nome', 'descrizione']
        widgets = {
            'descrizione': forms.Textarea(attrs={'rows': 2}),
        }

class ComponenteForm(ModelForm):
    class Meta:
        model = Componente
        # 'nome' è ora 'nome_componente' (ForeignKey a TipoComponente)
        # 'coppie_misure' è rimosso, gestito da MisuraComponenteFormSet
        fields = ['modello', 'nome_componente', 'colore', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class MisuraComponenteForm(ModelForm):
    class Meta:
        model = MisuraComponente
        fields = ['coppia_misura',] # Aggiungi altri campi se presenti in MisuraComponente
        # Potresti voler personalizzare il widget per coppia_misura se necessario
        # Esempio: far visualizzare solo CoppiaMisure non ancora associate a questo componente
        # widgets = {
        # 'coppia_misura': forms.Select(attrs={'class': 'select2'}),
        # }

# FormSet per gestire le MisuraComponente all'interno del form di Componente
MisuraComponenteFormSet = inlineformset_factory(
    Componente,
    MisuraComponente,
    form=MisuraComponenteForm,
    extra=1, # Numero di form vuoti aggiuntivi
    can_delete=True,
    fk_name='componente'
)


class ColoreForm(ModelForm):
    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex', 'descrizione']
        widgets = {
            'valore_hex': forms.TextInput(attrs={'type': 'color'}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }

# Aggiornato per il modello CoppiaMisura che ti ho fornito precedentemente
class CoppiaMisuraForm(ModelForm):
    class Meta:
        model = CoppiaMisura
        fields = ['descrizione_misura', 'numero_scarpa_riferimento', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'descrizione_misura': forms.TextInput(attrs={'placeholder': "Es. Taglia 42 per Scarpa, Lunghezza 30cm per Suola"}),
        }


class OrdineForm(ModelForm):
    class Meta:
        model = Ordine
        fields = ['modello', 'data_ordine', 'stato', 'note']
        widgets = {
            'data_ordine': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class DettaglioOrdineForm(ModelForm):
    class Meta:
        model = DettaglioOrdine
        # Il campo è stato rinominato in 'coppia_misura_scarpa' nel modello che ti ho fornito
        fields = ['ordine', 'coppia_misura_scarpa', 'quantita', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }
        # Se 'ordine' deve essere nascosto quando usato in un formset
        # exclude = ('ordine',)


DettaglioOrdineFormSet = inlineformset_factory(
    Ordine, DettaglioOrdine,
    form=DettaglioOrdineForm,
    extra=1,
    can_delete=True,
    fk_name='ordine'
)