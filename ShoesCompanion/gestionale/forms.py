from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Cliente, Modello, Componente, Colore, 
    CoppiaMisura, Ordine, DettaglioOrdine
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


class ComponenteForm(ModelForm):
    class Meta:
        model = Componente
        fields = ['modello', 'nome', 'colore', 'coppie_misure', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'coppie_misure': forms.SelectMultiple(attrs={'class': 'select2'}),
        }


class ColoreForm(ModelForm):
    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex', 'descrizione']
        widgets = {
            'valore_hex': forms.TextInput(attrs={'type': 'color'}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }


class CoppiaMisuraForm(ModelForm):
    class Meta:
        model = CoppiaMisura
        fields = ['numero_scarpa', 'larghezza', 'altezza', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class OrdineForm(ModelForm):
    class Meta:
        model = Ordine
        fields = ['modello', 'data_ordine', 'stato', 'note']
        widgets = {
            'data_ordine': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class DettaglioOrdineForm(ModelForm):
    class Meta:
        model = DettaglioOrdine
        fields = ['ordine', 'coppia_misura', 'quantita', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


DettaglioOrdineFormSet = inlineformset_factory(
    Ordine, DettaglioOrdine, 
    form=DettaglioOrdineForm,
    extra=1,
    can_delete=True
)