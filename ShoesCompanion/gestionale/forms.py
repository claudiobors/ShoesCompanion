from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import (
    Cliente, Modello, Componente, Colore, Ordine, DettaglioOrdine,
    TipoComponente, Taglia, Articolo
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

from .models import Modello, StrutturaModello # Aggiungi StrutturaModello

class ModelloForm(forms.ModelForm):
    # Aggiungiamo il campo per selezionare la struttura
    struttura = forms.ModelChoiceField(
        queryset=StrutturaModello.objects.all(),
        required=True,
        label="Scegli la struttura di base del modello",
        help_text="Questo pre-compilerà il modello con i componenti standard."
    )

    class Meta:
        model = Modello
        fields = ['cliente', 'nome', 'struttura', 'tipo', 'foto', 'note'] # Aggiungi 'struttura'

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
            # Usiamo il widget HTML5 nativo per la selezione del colore
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

class ComponenteForm(forms.ModelForm):
    """
    Form per creare o modificare un Componente associato a un Modello.
    Il campo 'modello' viene solitamente nascosto o pre-impostato nella vista.
    """
    class Meta:
        model = Componente
        fields = ['modello', 'nome_componente', 'colore', 'note']
        widgets = {
            'modello': forms.HiddenInput(), # Nascosto, verrà gestito dalla vista
            'nome_componente': forms.Select(attrs={'class': 'form-select'}),
            'colore': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

## Form e Formset per Articolo (Misura)

class ArticoloForm(forms.ModelForm):
    """
    Form per la singola misura di un componente per una data taglia,
    con validazione avanzata e widget migliorati.
    """
    class Meta:
        model = Articolo
        fields = ['taglia', 'superficie_mq', 'superficie_piedi_quadri']

        # Etichette più chiare per i campi del form
        labels = {
            'taglia': 'Taglia',
            'superficie_mq': 'Superficie (m²)',
            'superficie_piedi_quadri': 'Superficie (Piedi²)',
        }

        # Widget con attributi aggiuntivi per una migliore UX
        widgets = {
            'taglia': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'superficie_mq': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-sm text-end',
                    'placeholder': 'es. 0.1250',
                    'step': '0.0001'  # Permette incrementi decimali precisi
                }
            ),
            'superficie_piedi_quadri': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-sm text-end',
                    'placeholder': 'es. 1.3452',
                    'step': '0.0001'  # Permette incrementi decimali precisi
                }
            ),
        }

        # Testi di aiuto per guidare l'utente
        help_texts = {
            'superficie_mq': "Lasciare vuoto se si inseriscono i Piedi Quadrati.",
            'superficie_piedi_quadri': "Lasciare vuoto se si inseriscono i Metri Quadrati.",
        }

    def clean(self):
        """
        Controlla che almeno uno dei due campi superficie sia stato compilato,
        fornendo un errore a livello di form se entrambi sono vuoti.
        """
        cleaned_data = super().clean()
        mq = cleaned_data.get('superficie_mq')
        piedi = cleaned_data.get('superficie_piedi_quadri')

        if mq is None and piedi is None:
            # Questo errore verrà mostrato in cima al formset, è più generale.
            raise ValidationError(
                "È obbligatorio specificare un valore per almeno uno dei due campi di superficie (m² o Piedi²).",
                code='superficie_richiesta'
            )

        return cleaned_data

ArticoloFormSet = inlineformset_factory(
    Componente,
    Articolo,
    form=ArticoloForm,
    fields=('taglia', 'superficie_mq', 'superficie_piedi_quadri'),
    extra=1,
    can_delete=True,
    # min_num=1 # Opzionale: richiede almeno una misura per componente
)


## Form per Ordini

class OrdineMainForm(forms.ModelForm):
    """Form per i dati principali dell'Ordine."""
    class Meta:
        model = Ordine
        fields = ['modello', 'data_ordine', 'stato', 'note']
        widgets = {
            'modello': forms.Select(attrs={'class': 'form-select'}),
            'data_ordine': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class DettaglioOrdineForm(forms.ModelForm):
    """Form per la singola riga di dettaglio di un ordine."""
    class Meta:
        model = DettaglioOrdine
        fields = ['taglia', 'quantita', 'note']
        widgets = {
            'taglia': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantita': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '1'}),
            'note': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }

# Definiamo il Formset per i dettagli dell'ordine
DettaglioOrdineFormSet = forms.inlineformset_factory(
    Ordine,
    DettaglioOrdine,
    form=DettaglioOrdineForm,
    extra=1, # Parte con 1 form vuoto
    can_delete=True, # Permette di eliminare i dettagli esistenti
    min_num=1, # Richiede che ci sia almeno una riga di dettaglio
)

class QuantitaPerTagliaForm(forms.Form):
    """
    Un form che crea dinamicamente un campo per la quantità per ogni taglia.
    """
    def __init__(self, *args, **kwargs):
        # Rimuove 'instance' se presente, non ci serve per questo form
        kwargs.pop('instance', None) 
        
        super().__init__(*args, **kwargs)
        
        # Recupera tutte le taglie ordinate per numero
        taglie = Taglia.objects.all().order_by('numero')

        # Per ogni taglia, crea un campo numerico nel form
        for taglia in taglie:
            field_name = f'taglia_{taglia.pk}'
            self.fields[field_name] = forms.IntegerField(
                label=f"Taglia {taglia.numero}",
                required=False,
                min_value=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control form-control-sm text-center', 
                    'placeholder': '0',
                    'min': '0'
                }),
                initial=0
            )

    def get_dettagli_data(self):
        """
        Metodo helper per estrarre i dati delle quantità inserite.
        """
        for name, value in self.cleaned_data.items():
            if name.startswith('taglia_') and value is not None and value > 0:
                taglia_id = int(name.split('_')[1])
                yield (taglia_id, value)

class StrutturaModelloForm(forms.ModelForm):
    class Meta:
        model = StrutturaModello
        fields = ['nome', 'tipi_componente']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipi_componente': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'tipi_componente': "Seleziona tutti i componenti che devono essere creati di base per questa struttura."
        }

from django.forms import inlineformset_factory

ComponentePerOrdineFormSet = inlineformset_factory(
    Modello,
    Componente,
    fields=('nome_componente', 'colore', 'note'),
    extra=1, # MODIFICATO: Permette di aggiungere nuove righe
    can_delete=True, # AGGIUNTO: Permette di eliminare le righe
    widgets={
        'nome_componente': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        'colore': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        'note': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 1}),
    }
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