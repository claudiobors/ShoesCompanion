from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Cliente, Modello, Componente, Colore, Ordine, DettaglioOrdine,
    TipoComponente, Taglia, Articolo # Modelli aggiornati
)


class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'numero_telefono', 'indirizzo', 'partita_IVA', 'note']

class ModelloForm(ModelForm):
    class Meta:
        model = Modello
        fields = ['cliente', 'nome', 'tipo', 'foto', 'note']

class TipoComponenteForm(ModelForm):
    class Meta:
        model = TipoComponente
        fields = ['nome', 'descrizione']

class ColoreForm(ModelForm):
    class Meta:
        model = Colore
        fields = ['nome', 'valore_hex', 'descrizione']

class TagliaForm(ModelForm):
    class Meta:
        model = Taglia
        fields = ['numero', 'note']

class ComponenteForm(ModelForm):
    class Meta:
        model = Componente
        fields = ['modello', 'nome_componente', 'colore', 'note']

# --- FORM MANCANTE AGGIUNTO QUI ---
class ArticoloForm(ModelForm):
    class Meta:
        model = Articolo
        fields = ['taglia', 'descrizione_misura']
        widgets = {
            'descrizione_misura': forms.TextInput(attrs={'placeholder': "Es. Lunghezza 28cm, Spessore 5mm"}),
        }

ArticoloFormSet = inlineformset_factory(
    Componente,
    Articolo,
    form=ArticoloForm,  # Ora usa il nostro form personalizzato
    fields=('taglia', 'descrizione_misura'),
    extra=1,
    can_delete=True
)

class OrdineForm(ModelForm):
    class Meta:
        model = Ordine
        fields = ['modello', 'data_ordine', 'stato', 'note']

class DettaglioOrdineForm(ModelForm):
    class Meta:
        model = DettaglioOrdine
        fields = ['taglia', 'quantita', 'note']

DettaglioOrdineFormSet = inlineformset_factory(
    Ordine,
    DettaglioOrdine,
    form=DettaglioOrdineForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)