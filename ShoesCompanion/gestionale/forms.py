from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Cliente, Modello, Componente, Colore, Ordine, DettaglioOrdine,
    TipoComponente, Taglia, Articolo
)

# --- Form Anagrafiche e Configurazione ---
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'numero_telefono', 'indirizzo', 'partita_IVA', 'note']

class ModelloForm(forms.ModelForm):
    class Meta:
        model = Modello
        fields = ['cliente', 'nome', 'tipo', 'foto', 'note']

class TipoComponenteForm(forms.ModelForm):
    class Meta:
        model = TipoComponente
        fields = ['nome', 'descrizione']

class ColoreForm(forms.ModelForm):
    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex', 'descrizione']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            # Usiamo il widget HTML5 nativo per la selezione del colore,
            # aggiungendo la classe Bootstrap specifica 'form-control-color'
            'valore_hex': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nome': 'Nome Colore',
            'valore_hex': 'Seleziona Colore',
            'descrizione': 'Descrizione (opzionale)'
        }

class TagliaForm(forms.ModelForm):
    class Meta:
        model = Taglia
        fields = ['numero', 'note']

class ComponenteForm(forms.ModelForm):
    class Meta:
        model = Componente
        fields = ['modello', 'nome_componente', 'colore', 'note']

# --- FORM ARTICOLO CORRETTO ---
class ArticoloForm(forms.ModelForm):
    class Meta:
        model = Articolo
        # Usa i nuovi campi 'altezza' e 'larghezza' al posto di 'descrizione_misura'
        fields = ['taglia', 'altezza', 'larghezza']
        widgets = {
            'altezza': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Altezza in mm'}),
            'larghezza': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Larghezza in mm'}),
        }

ArticoloFormSet = inlineformset_factory(
    Componente,
    Articolo,
    form=ArticoloForm,
    fields=('taglia', 'altezza', 'larghezza'),
    extra=1,
    can_delete=True
)


# --- Form Ordini ---

class QuantitaPerTagliaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        dettagli_esistenti = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        taglie = Taglia.objects.all().order_by('numero')
        dettagli_map = {d.taglia.pk: d.quantita for d in dettagli_esistenti} if dettagli_esistenti else {}
        for taglia in taglie:
            self.fields[f'taglia_{taglia.pk}'] = forms.IntegerField(
                label=f"Taglia {taglia.numero}",
                required=False,
                min_value=0,
                initial=dettagli_map.get(taglia.pk, 0),
                widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm text-center', 'min': '0'})
            )
    def get_dettagli_data(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('taglia_') and value is not None:
                yield (int(name.split('_')[1]), value)

class OrdineMainForm(forms.ModelForm):
    """Form per i dati principali dell'Ordine."""
    class Meta:
        model = Ordine
        fields = ['modello', 'data_ordine', 'stato', 'note']
        widgets = {
            'data_ordine': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class DettaglioOrdineForm(forms.ModelForm):
    """Form per la singola riga di dettaglio."""
    class Meta:
        model = DettaglioOrdine
        fields = ['taglia', 'quantita', 'note']

# Definiamo il Formset che useremo nelle viste
DettaglioOrdineFormSet = forms.inlineformset_factory(
    Ordine,
    DettaglioOrdine,
    form=DettaglioOrdineForm,
    extra=1, # Parte con 1 form vuoto
    can_delete=True, # Permette di eliminare i dettagli esistenti
    # Non mettiamo 'min_num' qui, la logica sarà nella vista
)
