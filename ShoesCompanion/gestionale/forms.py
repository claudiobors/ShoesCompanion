from django import forms
from .models import (
    Cliente, Modello, Componente, Colore, Ordine, DettaglioOrdine,
    TipoComponente, Taglia, Articolo
)

class ClienteForm(forms.ModelForm):
    class Meta: model = Cliente; fields = ['nome', 'numero_telefono', 'indirizzo', 'partita_IVA', 'note']
class ModelloForm(forms.ModelForm):
    class Meta: model = Modello; fields = ['cliente', 'nome', 'tipo', 'foto', 'note']
class TipoComponenteForm(forms.ModelForm):
    class Meta: model = TipoComponente; fields = ['nome', 'descrizione']
class ColoreForm(forms.ModelForm):
    class Meta: model = Colore; fields = ['nome', 'valore_hex', 'descrizione']
class TagliaForm(forms.ModelForm):
    class Meta: model = Taglia; fields = ['numero', 'note']
class ComponenteForm(forms.ModelForm):
    class Meta: model = Componente; fields = ['modello', 'nome_componente', 'colore', 'note']
class ArticoloForm(forms.ModelForm):
    class Meta: model = Articolo; fields = ['taglia', 'descrizione_misura']

# --- Form Ordini ---
class OrdineMainForm(forms.ModelForm):
    class Meta:
        model = Ordine
        fields = ['modello', 'data_ordine', 'stato', 'note']
        widgets = {'data_ordine': forms.DateTimeInput(attrs={'type': 'datetime-local'}), 'note': forms.Textarea(attrs={'rows': 3})}

class QuantitaPerTagliaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        dettagli_esistenti = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        taglie = Taglia.objects.all().order_by('numero')
        dettagli_map = {d.taglia.pk: d.quantita for d in dettagli_esistenti} if dettagli_esistenti else {}
        for taglia in taglie:
            self.fields[f'taglia_{taglia.pk}'] = forms.IntegerField(label=f"Taglia {taglia.numero}", required=False, min_value=0, initial=dettagli_map.get(taglia.pk, 0), widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm text-center', 'min': '0'}))
    def get_dettagli_data(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('taglia_') and value is not None: yield (int(name.split('_')[1]), value)

# --- Form per Dettaglio Singolo ---
class DettaglioOrdineForm(forms.ModelForm):
    class Meta:
        model = DettaglioOrdine
        fields = ['taglia', 'quantita', 'note']