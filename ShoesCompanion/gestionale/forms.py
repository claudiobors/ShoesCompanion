from django import forms
from django.forms import inlineformset_factory
from .models import (
    Cliente, Modello, Componente, Colore, Ordine, DettaglioOrdine,
    TipoComponente, Taglia, Articolo, StrutturaModello
)

# --- Form Anagrafiche e Configurazione ---

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'numero_telefono', 'indirizzo', 'partita_IVA', 'note']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'indirizzo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'partita_IVA': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ModelloForm(forms.ModelForm):
    struttura = forms.ModelChoiceField(
        queryset=StrutturaModello.objects.all(),
        required=False,
        label="Scegli una struttura per pre-compilare i componenti",
        help_text="Selezionando una struttura, il modello verrà creato con i suoi componenti di base.",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Modello
        # Aggiunti i nuovi campi e rimosse le stringhe a caso
        fields = [
            'cliente', 'nome', 'codice_articolo', 'tipo', 'forma', 
            'struttura', 'foto', 'note'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codice_articolo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'forma': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TipoComponenteForm(forms.ModelForm):
    class Meta:
        model = TipoComponente
        fields = ['nome', 'descrizione']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ColoreForm(forms.ModelForm):
    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex', 'descrizione']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
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
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# --- Form Componenti e Articoli (MODIFICATI) ---

class ComponenteForm(forms.ModelForm):
    class Meta:
        model = Componente
        # AGGIUNTI I NUOVI CAMPI
        fields = [
            'modello', 'nome_componente', 'unita_misura', 'colore', 
            'descrizione', 'cod_componente', 'cod_colore', 'note'
        ]
        widgets = {
            'modello': forms.HiddenInput(),
            'nome_componente': forms.Select(attrs={'class': 'form-select'}),
            'unita_misura': forms.Select(attrs={'class': 'form-select'}),
            'colore': forms.Select(attrs={'class': 'form-select'}),
            # WIDGET PER I NUOVI CAMPI
            'descrizione': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. Pelle di vitello liscia'}),
            'cod_componente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codice Art. Fornitore'}),
            'cod_colore': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codice Colore Fornitore'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# MODIFICATO PER ESSERE DINAMICO
class ArticoloForm(forms.ModelForm):
    class Meta:
        model = Articolo
        fields = ['taglia', 'superficie_mq', 'superficie_piedi_quadri', 'quantita_unitaria']
        labels = {
            'superficie_mq': 'Superficie (m²)',
            'superficie_piedi_quadri': 'Superficie (ft²)',
            'quantita_unitaria': 'Quantità',
        }
        widgets = {
            'taglia': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'superficie_mq': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'placeholder': '0.1250', 'step': '0.0001'}),
            'superficie_piedi_quadri': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'placeholder': 'Calcolata in auto', 'step': '0.0001'}),
            'quantita_unitaria': forms.NumberInput(attrs={'class': 'form-control form-control-sm text-end', 'placeholder': '1.00', 'step': '0.01'}),
        }

ArticoloFormSet = inlineformset_factory(
    Componente,
    Articolo,
    form=ArticoloForm,
    fields=('taglia', 'superficie_mq', 'superficie_piedi_quadri', 'quantita_unitaria'),
    extra=1,
    can_delete=True
)



# --- Form e Formset per Ordini ---

class OrdineMainForm(forms.ModelForm):
    class Meta:
        model = Ordine
        # Aggiunto il campo data_consegna
        fields = ['modello', 'data_ordine', 'data_consegna', 'stato', 'note']
        widgets = {
            'modello': forms.Select(attrs={'class': 'form-select'}),
            'data_ordine': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'data_consegna': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), # Widget per DateField
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class DettaglioOrdineForm(forms.ModelForm):
    class Meta:
        model = DettaglioOrdine
        fields = ['taglia', 'quantita', 'note']
        widgets = {
            'taglia': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantita': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '1'}),
            'note': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

DettaglioOrdineFormSet = inlineformset_factory(
    Ordine,
    DettaglioOrdine,
    form=DettaglioOrdineForm,
    extra=1,
    can_delete=True,
    min_num=1
)

class QuantitaPerTagliaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        taglie = Taglia.objects.all().order_by('numero')
        for taglia in taglie:
            self.fields[f'taglia_{taglia.pk}'] = forms.IntegerField(
                label=f"T. {taglia}",
                required=False,
                min_value=0,
                initial=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control form-control-sm text-center',
                    'placeholder': '0',
                    'min': '0'
                })
            )

    def get_dettagli_data(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('taglia_') and value and value > 0:
                yield (int(name.split('_')[1]), value)

class StrutturaModelloForm(forms.ModelForm):
    class Meta:
        model = StrutturaModello
        fields = ['nome', 'tipi_componente']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipi_componente': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'tipi_componente': "Seleziona i componenti base per questa struttura."
        }

ComponentePerOrdineFormSet = inlineformset_factory(
    Modello,
    Componente,
    form=ComponenteForm,
    # AGGIUNGI 'unita_misura' a questa lista
    fields=('nome_componente', 'unita_misura', 'colore', 'note'),
    extra=1,
    can_delete=True
)

class BollaSplitForm(forms.Form):
    max_totale = forms.IntegerField(
        label="Numero totale massimo di paia per bolla",
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Es. 10'})
    )
    max_per_taglia = forms.IntegerField(
        label="Numero massimo di paia per singola taglia per bolla",
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Es. 2'}),
        help_text="Lascia vuoto per non impostare un limite per taglia."
    )