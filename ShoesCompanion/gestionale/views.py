from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.forms import inlineformset_factory
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.utils import timezone

from io import BytesIO
from reportlab.pdfgen import canvas

from decimal import Decimal

from .filters import (ClienteFilter, ColoreFilter, ComponenteFilter,
                    ModelloFilter, OrdineFilter, TagliaFilter,
                    TipoComponenteFilter)
from .forms import (ClienteForm, ColoreForm, ComponenteForm, DettaglioOrdineForm,
                    ModelloForm, OrdineMainForm, DettaglioOrdineFormSet, ArticoloFormSet,
                    TagliaForm, TipoComponenteForm)
from .models import (Articolo, Cliente, Colore, Componente, DettaglioOrdine,
                   Modello, Ordine, Taglia, TipoComponente)
from .tables import (ClienteTable, ColoreTable, ModelloTable, OrdineTable,
                   TagliaTable, TipoComponenteTable)

# ==============================================================================
# VISTA HOME
# ==============================================================================
@login_required
def home(request):
    """Mostra la dashboard principale con le statistiche."""
    context = {
        'clienti_count': Cliente.objects.count(),
        'modelli_count': Modello.objects.count(),
        'tipi_componente_count': TipoComponente.objects.count(),
        'ordini_attivi_count': Ordine.objects.exclude(stato__in=['COMPLETATO', 'ANNULLATO']).count(),
        'scarpe_da_produrre': DettaglioOrdine.objects.filter(ordine__stato='CONFERMATO').aggregate(total=Sum('quantita'))['total'] or 0,
        'ordini_recenti': Ordine.objects.select_related('modello', 'modello__cliente').order_by('-data_ordine')[:5],
    }
    stati_ordine_data = Ordine.objects.values('stato').annotate(count=Count('id')).order_by('stato')
    stati_grafico = {stato_key: 0 for stato_key, stato_display in Ordine.STATO_ORDINE_CHOICES}
    for item in stati_ordine_data:
        if item['stato'] in stati_grafico:
            stati_grafico[item['stato']] = item['count']
    context['stati_ordine_grafico'] = stati_grafico
    return render(request, 'gestionale/home.html', context)


# ==============================================================================
# VISTE CRUD PRINCIPALI
# ==============================================================================

# --- Viste Cliente ---
class ClienteListView(LoginRequiredMixin, generic.ListView):
    model = Cliente
    template_name = 'gestionale/clienti/cliente_list.html'
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = ClienteFilter(self.request.GET, queryset=self.get_queryset())
        context['table'] = ClienteTable(context['filter'].qs)
        return context

class ClienteDetailView(LoginRequiredMixin, generic.DetailView):
    model = Cliente
    template_name = 'gestionale/clienti/cliente_detail.html'

class ClienteCreateView(LoginRequiredMixin, generic.CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'gestionale/clienti/cliente_form.html'
    success_url = reverse_lazy('cliente_list')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'gestionale/clienti/cliente_form.html'
    def get_success_url(self):
        return reverse('cliente_detail', kwargs={'pk': self.object.pk})

class ClienteDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Cliente
    template_name = 'gestionale/clienti/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')


# --- Viste Modello ---
class ModelloListView(LoginRequiredMixin, generic.ListView):
    model = Modello
    template_name = 'gestionale/modelli/modello_list.html'
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset().select_related('cliente')
        context['filter'] = ModelloFilter(self.request.GET, queryset=queryset)
        context['table'] = ModelloTable(context['filter'].qs)
        return context

class ModelloDetailView(LoginRequiredMixin, generic.DetailView):
    model = Modello
    template_name = 'gestionale/modelli/modello_detail.html'

# In views.py
from .models import Modello, Componente # Aggiungi Componente
from django.db import transaction

class ModelloCreateView(LoginRequiredMixin, generic.CreateView):
    model = Modello
    form_class = ModelloForm
    template_name = 'gestionale/modelli/modello_form.html'
    
    def form_valid(self, form):
        # Il metodo form_valid viene eseguito solo se il form è già valido

        try:
            # Apriamo una transazione atomica: o tutto o niente.
            with transaction.atomic():
                # 1. Recupera la struttura scelta dal form PRIMA di salvare
                struttura_scelta = form.cleaned_data['struttura']

                # 2. Crea l'oggetto Modello in memoria (commit=False)
                #    Questo evita l'errore del campo 'struttura'
                self.object = form.save(commit=False)
                self.object.created_by = self.request.user
                
                # 3. Salva l'oggetto Modello principale nel database
                self.object.save()

                # 4. Ora che il modello esiste, crea i suoi componenti base
                tipi_componente_da_creare = struttura_scelta.tipi_componente.all()
                for tipo_comp in tipi_componente_da_creare:
                    Componente.objects.create(modello=self.object, nome_componente=tipo_comp)
        
        except Exception as e:
            # Se qualcosa va storto, mostra un messaggio di errore
            messages.error(self.request, f"Si è verificato un errore durante la creazione del modello: {e}")
            # Ricarica la pagina con i dati inseriti per non far perdere il lavoro all'utente
            return self.form_invalid(form)

        # Se tutto è andato a buon fine, mostra il messaggio di successo e reindirizza
        messages.success(self.request, f"Modello '{self.object.nome}' creato con i componenti di base. Ora puoi definirne i dettagli.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('modello_detail', kwargs={'pk': self.object.pk})

class ModelloUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Modello
    form_class = ModelloForm
    template_name = 'gestionale/modelli/modello_form.html'
    def get_success_url(self):
        return reverse('modello_detail', kwargs={'pk': self.object.pk})

class ModelloDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Modello
    template_name = 'gestionale/modelli/modello_confirm_delete.html'
    success_url = reverse_lazy('modello_list')

@login_required
def modello_duplicate(request, pk):
    modello = get_object_or_404(Modello, pk=pk)
    if request.method == 'POST':
        new_name = request.POST.get('new_name', f"{modello.nome} (Copia)")
        new_modello = modello.duplicate(new_name)
        return redirect('modello_detail', pk=new_modello.pk)
    return render(request, 'gestionale/modelli/modello_duplicate.html', {'modello': modello})


# --- Viste Componente e Articoli ---
class ComponenteCreateView(LoginRequiredMixin, generic.CreateView):
    model = Componente
    form_class = ComponenteForm
    template_name = 'gestionale/componenti/componente_form.html'
    def get_initial(self):
        initial = super().get_initial()
        if 'modello_id' in self.kwargs:
            initial['modello'] = get_object_or_404(Modello, pk=self.kwargs['modello_id'])
        return initial
    def get_success_url(self):
        return reverse('manage_articoli_componente', kwargs={'componente_id': self.object.pk})

class ComponenteUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Componente
    form_class = ComponenteForm
    template_name = 'gestionale/componenti/componente_form.html'
    def get_success_url(self):
        return reverse('modello_detail', kwargs={'pk': self.object.modello.pk})

class ComponenteDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Componente
    template_name = 'gestionale/componenti/componente_confirm_delete.html'
    def get_success_url(self):
        return reverse('modello_detail', kwargs={'pk': self.object.modello.pk})

@login_required
def manage_articoli_componente(request, componente_id):
    componente = get_object_or_404(Componente.objects.select_related('modello'), pk=componente_id)
    
    if request.method == 'POST':
        formset = ArticoloFormSet(request.POST, instance=componente, prefix='articoli')
        if formset.is_valid():
            formset.save()
            messages.success(request, "Misure salvate con successo.")
            return redirect('modello_detail', pk=componente.modello.pk)
        else:
            messages.error(request, "Errore nella compilazione dei dati. Controlla i campi evidenziati.")
    else:
        formset = ArticoloFormSet(instance=componente, prefix='articoli')
        
    # NUOVA LOGICA: Passiamo al template la lista di tutte le taglie
    tutte_le_taglie = Taglia.objects.all().order_by('numero')
    # Convertiamo i dati in un formato leggibile da JavaScript
    taglie_data_for_js = [{'id': t.id, 'numero': str(t)} for t in tutte_le_taglie]

    context = {
        'formset': formset, 
        'componente': componente,
        'tutte_le_taglie_js': taglie_data_for_js # NUOVO DATO PER IL TEMPLATE
    }
    return render(request, 'gestionale/componenti/manage_articoli.html', context)

# --- Viste Ordine ---
class OrdineListView(LoginRequiredMixin, generic.ListView):
    model = Ordine
    template_name = 'gestionale/ordini/ordine_list.html'
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Ordine.objects.select_related('modello', 'modello__cliente').all()
        context['filter'] = OrdineFilter(self.request.GET, queryset=queryset)
        context['table'] = OrdineTable(context['filter'].qs)
        return context

class OrdineDetailView(LoginRequiredMixin, generic.DetailView):
    model = Ordine
    template_name = 'gestionale/ordini/ordine_detail.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materiali_necessari'] = self.object.get_materiali_necessari()
        return context
    
from .forms import OrdineMainForm, QuantitaPerTagliaForm # Assicurati di importarlo


from .forms import OrdineMainForm, QuantitaPerTagliaForm, ComponentePerOrdineFormSet, QuantitaPerTagliaForm # Aggiungi il nuovo formset
from .models import Ordine, DettaglioOrdine, Taglia, Modello # Aggiungi Modello

class OrdineCreateView(LoginRequiredMixin, generic.CreateView):
    model = Ordine
    form_class = OrdineMainForm
    template_name = 'gestionale/ordini/ordine_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Se i form non sono già nel contesto, li aggiungiamo (caso GET)
        if 'componenti_formset' not in context:
            context['componenti_formset'] = ComponentePerOrdineFormSet(prefix='componenti', queryset=Componente.objects.none())
        if 'quantita_form' not in context:
            context['quantita_form'] = QuantitaPerTagliaForm(prefix='quantita')
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        quantita_form = QuantitaPerTagliaForm(request.POST, prefix='quantita')
        
        # Il formset dei componenti dipende dal modello selezionato nel POST
        modello_id = request.POST.get('modello')
        if not modello_id:
            form.add_error('modello', 'Questo campo è obbligatorio.')
            return self.form_invalid(form, None, quantita_form)
        
        modello_base = get_object_or_404(Modello, pk=modello_id)
        componenti_formset = ComponentePerOrdineFormSet(request.POST, instance=modello_base, prefix='componenti')

        if form.is_valid() and componenti_formset.is_valid() and quantita_form.is_valid():
            return self.form_valid(form, modello_base, componenti_formset, quantita_form)
        else:
            return self.form_invalid(form, componenti_formset, quantita_form)

    def form_valid(self, form, modello_base, componenti_formset, quantita_form):
        # La logica di form_valid che hai già scritto va qui...
        # (quella che controlla .has_changed(), duplica il modello, etc.)
        # ...assicurati che sia identica a quella della risposta precedente...
        modello_per_ordine = modello_base

        if componenti_formset.has_changed():
            nome_variante = f"{modello_base.nome} - V.{timezone.now().strftime('%y%m%d-%H%M')}"
            modello_variante = modello_base.duplicate(new_name=nome_variante, created_by=self.request.user)
            componenti_modificati = ComponentePerOrdineFormSet(self.request.POST, instance=modello_variante, prefix='componenti')
            if componenti_modificati.is_valid():
                componenti_modificati.save()
            modello_per_ordine = modello_variante
            messages.info(self.request, f"Creata una nuova variante del modello: '{nome_variante}'")

        ordine = form.save(commit=False)
        ordine.modello = modello_per_ordine
        ordine.created_by = self.request.user
        ordine.save()
        
        for taglia_id, quantita in quantita_form.get_dettagli_data():
            DettaglioOrdine.objects.create(ordine=ordine, taglia_id=taglia_id, quantita=quantita)
            
        messages.success(self.request, f"Ordine #{ordine.id} creato con successo.")
        return redirect(reverse('ordine_detail', kwargs={'pk': ordine.pk}))

    def form_invalid(self, form, componenti_formset, quantita_form):
        # Questo metodo ora si assicura che tutti i form (con i loro dati ed errori)
        # vengano passati correttamente al template per la visualizzazione.
        context = self.get_context_data(form=form, componenti_formset=componenti_formset, quantita_form=quantita_form)
        return self.render_to_response(context)

class OrdineUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Ordine
    form_class = OrdineMainForm
    template_name = 'gestionale/ordini/ordine_form.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['dettagli_formset'] = DettaglioOrdineFormSet(self.request.POST, instance=self.object, prefix='dettagli')
        else:
            data['dettagli_formset'] = DettaglioOrdineFormSet(instance=self.object, prefix='dettagli')
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        dettagli_formset = context['dettagli_formset']

        if not dettagli_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        # --- Logica Personalizzata per Sommare e Aggiornare ---
        taglie_aggregate = {}
        for dettaglio_form in dettagli_formset:
            if dettaglio_form.is_valid() and not dettaglio_form.cleaned_data.get('DELETE', False):
                taglia = dettaglio_form.cleaned_data.get('taglia')
                quantita = dettaglio_form.cleaned_data.get('quantita')
                if taglia and quantita:
                    taglie_aggregate[taglia] = taglie_aggregate.get(taglia, 0) + quantita

        self.object = form.save()

        # Sincronizza il database con i dati aggregati
        taglie_da_mantenere = []
        for taglia, quantita_totale in taglie_aggregate.items():
            dettaglio, created = DettaglioOrdine.objects.update_or_create(
                ordine=self.object,
                taglia=taglia,
                defaults={'quantita': quantita_totale}
            )
            taglie_da_mantenere.append(taglia.pk)

        # Elimina i dettagli per le taglie non più presenti nel form
        self.object.dettagli.exclude(taglia__pk__in=taglie_da_mantenere).delete()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.pk})

class OrdineDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Ordine
    template_name = 'gestionale/ordini/ordine_confirm_delete.html'
    success_url = reverse_lazy('ordine_list')

@login_required
def ordine_conferma(request, pk):
    if request.method == 'POST':
        ordine = get_object_or_404(Ordine, pk=pk)
        if ordine.stato == 'BOZZA':
            ordine.stato = 'CONFERMATO'
            ordine.save()
    return redirect('ordine_detail', pk=pk)

@login_required
def ordine_annulla(request, pk):
    if request.method == 'POST':
        ordine = get_object_or_404(Ordine, pk=pk)
        if ordine.stato in ['BOZZA', 'CONFERMATO']:
            ordine.stato = 'ANNULLATO'
            ordine.save()
    return redirect('ordine_detail', pk=pk)


# --- Viste Dettaglio Ordine ---
# In gestionale/views.py

# --- Viste Dettaglio Ordine ---
class DettaglioOrdineCreateView(LoginRequiredMixin, generic.CreateView):
    model = DettaglioOrdine
    form_class = DettaglioOrdineForm
    template_name = 'gestionale/ordini/dettaglioordine_form.html'

    def get_initial(self):
        initial = super().get_initial()
        if 'ordine_id' in self.kwargs:
            initial['ordine'] = get_object_or_404(Ordine, pk=self.kwargs['ordine_id'])
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'ordine_id' in self.kwargs:
            context['ordine'] = get_object_or_404(Ordine, pk=self.kwargs['ordine_id'])
        return context

    def form_valid(self, form):
        # Assegna l'ordine al dettaglio
        ordine = get_object_or_404(Ordine, pk=self.kwargs.get('ordine_id'))
        form.instance.ordine = ordine
        
        # --- LOGICA DI CONTROLLO DUPLICATI ---
        taglia = form.cleaned_data.get('taglia')
        
        # Controlla se un dettaglio per questa taglia esiste già per questo ordine
        dettaglio_esistente = DettaglioOrdine.objects.filter(ordine=ordine, taglia=taglia).first()
        
        if dettaglio_esistente:
            # Se esiste, aggiorna la quantità sommando quella nuova
            dettaglio_esistente.quantita += form.cleaned_data.get('quantita', 0)
            dettaglio_esistente.save()
            messages.success(self.request, f"Quantità per la taglia {taglia.numero} aggiornata con successo.")
            return redirect('ordine_detail', pk=ordine.pk)
        else:
            # Se non esiste, crea un nuovo dettaglio (comportamento standard)
            messages.success(self.request, "Nuovo dettaglio aggiunto con successo.")
            return super().form_valid(form)

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.ordine.pk})

class DettaglioOrdineUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = DettaglioOrdine
    form_class = DettaglioOrdineForm
    template_name = 'gestionale/ordini/dettaglioordine_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # CORREZIONE: Aggiunge l'ordine al contesto per usarlo nel template
        context['ordine'] = self.object.ordine
        return context

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.ordine.pk})

class DettaglioOrdineDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = DettaglioOrdine
    template_name = 'gestionale/ordini/dettaglioordine_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.ordine.pk})


# ==============================================================================
# VISTE OGGETTI DI CONFIGURAZIONE
# ==============================================================================

# --- Viste Colore ---
class ColoreListView(LoginRequiredMixin, generic.ListView):
    model = Colore
    template_name = 'gestionale/colori/colore_list.html'
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = ColoreFilter(self.request.GET, queryset=self.get_queryset())
        context['table'] = ColoreTable(context['filter'].qs)
        return context

class ColoreDetailView(LoginRequiredMixin, generic.DetailView):
    model = Colore
    template_name = 'gestionale/colori/colore_detail.html'

class ColoreCreateView(LoginRequiredMixin, generic.CreateView):
    model = Colore
    form_class = ColoreForm
    template_name = 'gestionale/colori/colore_form.html'
    success_url = reverse_lazy('colore_list')

class ColoreUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Colore
    form_class = ColoreForm
    template_name = 'gestionale/colori/colore_form.html'
    def get_success_url(self):
        return reverse('colore_detail', kwargs={'pk': self.object.pk})

class ColoreDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Colore
    template_name = 'gestionale/colori/colore_confirm_delete.html'
    success_url = reverse_lazy('colore_list')


# --- Viste Taglia ---
class TagliaListView(LoginRequiredMixin, generic.ListView):
    model = Taglia
    template_name = 'gestionale/taglie/taglia_list.html'
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = TagliaFilter(self.request.GET, queryset=self.get_queryset())
        context['table'] = TagliaTable(context['filter'].qs)
        return context

class TagliaDetailView(LoginRequiredMixin, generic.DetailView):
    model = Taglia
    template_name = 'gestionale/taglie/taglia_detail.html'

class TagliaCreateView(LoginRequiredMixin, generic.CreateView):
    model = Taglia
    form_class = TagliaForm
    template_name = 'gestionale/taglie/taglia_form.html'
    success_url = reverse_lazy('taglia_list')

class TagliaUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Taglia
    form_class = TagliaForm
    template_name = 'gestionale/taglie/taglia_form.html'
    def get_success_url(self):
        return reverse('taglia_detail', kwargs={'pk': self.object.pk})

class TagliaDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Taglia
    template_name = 'gestionale/taglie/taglia_confirm_delete.html'
    success_url = reverse_lazy('taglia_list')


# --- Viste TipoComponente ---
class TipoComponenteListView(LoginRequiredMixin, generic.ListView):
    model = TipoComponente
    template_name = 'gestionale/tipicomponente/tipocomponente_list.html'
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = TipoComponenteFilter(self.request.GET, queryset=self.get_queryset())
        context['table'] = TipoComponenteTable(context['filter'].qs)
        return context

class TipoComponenteDetailView(LoginRequiredMixin, generic.DetailView):
    model = TipoComponente
    template_name = 'gestionale/tipicomponente/tipocomponente_detail.html'

class TipoComponenteCreateView(LoginRequiredMixin, generic.CreateView):
    model = TipoComponente
    form_class = TipoComponenteForm
    template_name = 'gestionale/tipicomponente/tipocomponente_form.html'
    success_url = reverse_lazy('tipocomponente_list')

class TipoComponenteUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TipoComponente
    form_class = TipoComponenteForm
    template_name = 'gestionale/tipicomponente/tipocomponente_form.html'
    def get_success_url(self):
        return reverse('tipocomponente_detail', kwargs={'pk': self.object.pk})

class TipoComponenteDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = TipoComponente
    template_name = 'gestionale/tipicomponente/tipocomponente_confirm_delete.html'
    success_url = reverse_lazy('tipocomponente_list')


# ==============================================================================
# VISTE REPORT E PDF
# ==============================================================================

# Import per ReportLab / PDF
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# In gestionale/views.py
from decimal import Decimal # Assicurati che questo import sia presente all'inizio del file

@login_required
def report_dashboard(request):
    """
    Mostra una dashboard con analisi avanzate, incluso il calcolo
    totale dei materiali necessari per gli ordini attivi.
    """
    
    # --- 1. Calcolo Aggregato dei Materiali da Ordinare ---
    ordini_attivi = Ordine.objects.exclude(stato__in=['COMPLETATO', 'ANNULLATO'])
    
    materiali_da_ordinare = {}

    for ordine in ordini_attivi:
        materiali_per_ordine = ordine.get_materiali_necessari()
        
        for key, misure in materiali_per_ordine.items():
            # La riga seguente è la correzione chiave.
            # .setdefault() garantisce che 'master_entry' abbia sempre un valore.
            # Se la chiave (es. 'Tomaia', 'Pelle Nera') non esiste nel dizionario,
            # la crea con i valori di default. Altrimenti, restituisce quella esistente.
            master_entry = materiali_da_ordinare.setdefault(key, {
                'tot_superficie_mq': Decimal('0.0'),
                'tot_superficie_piedi_quadri': Decimal('0.0'),
                'unita_prodotte': 0
            })
            
            # Ora possiamo aggiungere i valori con la certezza che 'master_entry' esista.
            master_entry['tot_superficie_mq'] += misure.get('tot_superficie_mq', Decimal('0.0'))
            master_entry['tot_superficie_piedi_quadri'] += misure.get('tot_superficie_piedi_quadri', Decimal('0.0'))
            master_entry['unita_prodotte'] += misure.get('unita_prodotte', 0)

    # --- 2. Altre Statistiche (già corrette) ---
    ordini_per_stato_qs = Ordine.objects.values('stato').annotate(
        count=Count('id'),
        total_pairs=Sum('dettagli__quantita') 
    ).order_by('stato')
    
    modelli_popolari = Modello.objects.annotate(num_ordini=Count('ordini')).order_by('-num_ordini')[:5]
    clienti_attivi = Cliente.objects.annotate(num_ordini=Count('modelli__ordini')).order_by('-num_ordini')[:5]

    context = {
        'materiali_da_ordinare': materiali_da_ordinare,
        'ordini_per_stato': list(ordini_per_stato_qs),
        'modelli_popolari': modelli_popolari,
        'clienti_attivi': clienti_attivi,
        'stato_choices': dict(Ordine.STATO_ORDINE_CHOICES)
    }
    return render(request, 'gestionale/report/dashboard.html', context)

def _pdf_base_elements(title_text):
    """Funzione helper per creare stili e titolo comuni per i PDF."""
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(name='Title', fontSize=20, alignment=TA_CENTER, spaceBottom=20, fontName='Helvetica-Bold')
    style_heading = ParagraphStyle(name='Heading2', fontSize=14, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    
    elements = [Paragraph(title_text, style_title)]
    return elements, styles

@login_required
def bolla_ordine_pdf(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    elements, styles = _pdf_base_elements("Bolla d'Ordine")
    
    # Dati Ordine
    data_ordine = [
        [Paragraph("<b>Ordine N:</b>", styles['Normal']), Paragraph(f"#{ordine.id}", styles['Normal'])],
        [Paragraph("<b>Data Ordine:</b>", styles['Normal']), Paragraph(ordine.data_ordine.strftime('%d/%m/%Y'), styles['Normal'])],
        [Paragraph("<b>Cliente:</b>", styles['Normal']), Paragraph(ordine.modello.cliente.nome, styles['Normal'])],
        [Paragraph("<b>Modello:</b>", styles['Normal']), Paragraph(ordine.modello.nome, styles['Normal'])],
    ]
    table_info = Table(data_ordine, colWidths=[3*cm, None])
    table_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(table_info)
    elements.append(Spacer(1, 1*cm)) # Aggiunge spazio verticale

    # Dettagli Taglie
    elements.append(Paragraph("Dettagli Quantità per Taglia", styles['h2']))
    
    data_dettagli = [["Taglia", "Quantità", "Note"]]
    for dettaglio in ordine.dettagli.all().order_by('taglia__numero'):
        data_dettagli.append([str(dettaglio.taglia), str(dettaglio.quantita), dettaglio.note or ''])
    
    data_dettagli.append(["", "", ""]) # Riga vuota di spaziatura
    data_dettagli.append([Paragraph("<b>TOTALE PAIA</b>", styles['Normal']), Paragraph(f"<b>{ordine.quantita_totale}</b>", styles['Normal']), ""])
    
    table_dettagli = Table(data_dettagli, colWidths=[4*cm, 4*cm, 7*cm])
    table_dettagli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
        ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-2), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table_dettagli)
    
    doc.build(elements)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bolla_ordine_{pk}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response

@login_required
def scheda_materiali_pdf(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    materiali = ordine.get_materiali_necessari()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    elements, styles = _pdf_base_elements("Scheda Materiali Necessari")
    
    elements.append(Paragraph(f"<b>Ordine:</b> #{ordine.id} - <b>Modello:</b> {ordine.modello.nome}", styles['Normal']))
    elements.append(Spacer(1, 1*cm))

    # Tabella Materiali
    data_materiali = [["Componente", "Colore", "Unità", "Sup. Tot (m²)", "Sup. Tot (Piedi²)"]]
    
    for key, misure in materiali.items():
        nome_componente, colore = key
        data_materiali.append([
            Paragraph(nome_componente, styles['BodyText']),
            Paragraph(colore.nome if colore else "-", styles['BodyText']),
            misure['unita_prodotte'],
            f"{misure.get('tot_superficie_mq', 0):.4f}",
            f"{misure.get('tot_superficie_piedi_quadri', 0):.4f}",
        ])
        
    table_materiali = Table(data_materiali)
    table_materiali.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.royalblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table_materiali)
    
    doc.build(elements)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="scheda_materiali_{pk}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response

@login_required
def scheda_modello_pdf(request, pk):
    modello = get_object_or_404(Modello, pk=pk)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5*cm, bottomMargin=2.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    
    elements, styles = _pdf_base_elements("Scheda Tecnica Modello")
    
    # Dati Modello e Foto
    info_data = [
        [
            Paragraph(f"<b>Modello:</b> {modello.nome}<br/>"
                      f"<b>Cliente:</b> {modello.cliente.nome}<br/>"
                      f"<b>Tipo:</b> {modello.get_tipo_display()}", styles['Normal']),
            Image(modello.foto.path, width=4*cm, height=4*cm) if modello.foto else Paragraph("Nessuna Foto", styles['Italic'])
        ]
    ]
    info_table = Table(info_data, colWidths=[10*cm, 5*cm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(info_table)
    elements.append(Spacer(1, 1*cm))
    
    # Componenti e Misure
    elements.append(Paragraph("Componenti e Misure per Taglia", styles['h2']))
    
    for componente in modello.componenti.all():
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"<b>Componente:</b> {componente.nome_componente.nome} - <b>Colore:</b> {componente.colore or '-'}", styles['h3']))
        
        articoli = componente.articoli.all().order_by('taglia__numero')
        if articoli:
            data_articoli = [["Taglia", "Superficie (m²)", "Superficie (Piedi²)"]]
            for articolo in articoli:
                mq_str = f"{articolo.superficie_mq:.4f}" if articolo.superficie_mq is not None else "N/D"
                pq_str = f"{articolo.superficie_piedi_quadri:.4f}" if articolo.superficie_piedi_quadri is not None else "N/D"
                data_articoli.append([str(articolo.taglia), mq_str, pq_str])
            
            table_articoli = Table(data_articoli, colWidths=[4*cm, 4*cm, 4*cm])
            table_articoli.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 0.5, colors.darkgrey),
                ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ]))
            elements.append(table_articoli)
        else:
            elements.append(Paragraph("Nessuna misura specifica definita per questo componente.", styles['Italic']))

    if modello.note:
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Note sul Modello", styles['h2']))
        elements.append(Paragraph(modello.note.replace('\n', '<br/>'), styles['BodyText']))
        
    doc.build(elements)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="scheda_modello_{pk}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response

from .models import StrutturaModello # Aggiungi l'import
from .forms import StrutturaModelloForm # Aggiungi l'import

    # --- Viste StrutturaModello ---
class StrutturaModelloListView(LoginRequiredMixin, generic.ListView):
    model = StrutturaModello
    template_name = 'gestionale/strutture/strutturamodello_list.html'
    context_object_name = 'strutture'

class StrutturaModelloDetailView(LoginRequiredMixin, generic.DetailView):
    model = StrutturaModello
    template_name = 'gestionale/strutture/strutturamodello_detail.html'

class StrutturaModelloCreateView(LoginRequiredMixin, generic.CreateView):
    model = StrutturaModello
    form_class = StrutturaModelloForm
    template_name = 'gestionale/strutture/strutturamodello_form.html'
    success_url = reverse_lazy('strutturamodello_list')

class StrutturaModelloUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = StrutturaModello
    form_class = StrutturaModelloForm
    template_name = 'gestionale/strutture/strutturamodello_form.html'
    success_url = reverse_lazy('strutturamodello_list')

class StrutturaModelloDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = StrutturaModello
    template_name = 'gestionale/strutture/strutturamodello_confirm_delete.html'
    success_url = reverse_lazy('strutturamodello_list')

    from django.shortcuts import render

def load_modello_components(request, modello_id):
    modello = get_object_or_404(Modello, pk=modello_id)
    componenti_formset = ComponentePerOrdineFormSet(instance=modello, prefix='componenti')
    return render(request, 'gestionale/ordini/partials/componenti_formset.html', {'componenti_formset': componenti_formset})

def crea_distribuzione_bolle(dettagli_ordine, max_totale, max_per_taglia=None):
    """
    Algoritmo per suddividere un ordine in bolle di lavoro ottimizzate.
    """
    bolle = []
    # Crea un dizionario con le quantità rimanenti da distribuire, ordinato per taglia
    da_distribuire = {
        d.taglia: d.quantita 
        for d in dettagli_ordine.order_by('taglia__numero')
    }

    while any(q > 0 for q in da_distribuire.values()):
        nuova_bolla = {}
        paia_in_bolla = 0
        
        for taglia, quantita_rimanente in da_distribuire.items():
            if quantita_rimanente == 0:
                continue

            # Calcola quanti paia di questa taglia possiamo aggiungere
            limite_taglia = max_per_taglia if max_per_taglia else quantita_rimanente
            spazio_disponibile = max_totale - paia_in_bolla
            
            da_aggiungere = min(quantita_rimanente, limite_taglia, spazio_disponibile)

            if da_aggiungere > 0:
                nuova_bolla[taglia] = da_aggiungere
                paia_in_bolla += da_aggiungere
                da_distribuire[taglia] -= da_aggiungere
        
        if nuova_bolla:
            bolle.append(nuova_bolla)
            
    return bolle

from django.views.generic.edit import FormView
from .forms import BollaSplitForm
from .models import Ordine
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER


# In gestional/views.py

# 1. AGGIUNGI 'landscape' AGLI IMPORT DI REPORTLAB
from reportlab.lib.pagesizes import A4, landscape
# Aggiungi 'ceil' agli import all'inizio del file
from math import ceil


# Aggiungi 'Image' agli import di reportlab
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image

class GeneraBolleView(LoginRequiredMixin, FormView):
    form_class = BollaSplitForm
    template_name = 'gestionale/ordini/genera_bolle_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ordine'] = get_object_or_404(Ordine, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        ordine = get_object_or_404(Ordine, pk=self.kwargs['pk'])
        max_totale = form.cleaned_data['max_totale']
        max_per_taglia = form.cleaned_data.get('max_per_taglia')

        dettagli = ordine.dettagli.all()
        bolle_distribuite = crea_distribuzione_bolle(dettagli, max_totale, max_per_taglia)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
        styles = getSampleStyleSheet()
        style_bold = ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold')
        
        elements = []
        
        total_bolle = len(bolle_distribuite)
        componenti_del_modello = list(ordine.modello.componenti.select_related('nome_componente', 'colore').all())

        for i, bolla in enumerate(bolle_distribuite, 1):
            elements.append(Paragraph(f"Bolla di Lavoro {i} di {total_bolle}", styles['h2']))
            
            info_data = [
                [Paragraph('<b>Cliente:</b>', styles['Normal']), Paragraph(ordine.modello.cliente.nome, styles['Normal'])],
                [Paragraph('<b>Modello:</b>', styles['Normal']), Paragraph(ordine.modello.nome, styles['Normal'])],
                [Paragraph('<b>Data Ordine:</b>', styles['Normal']), Paragraph(ordine.data_ordine.strftime('%d/%m/%Y'), styles['Normal'])],
            ]
            info_table_sx = Table(info_data, colWidths=[3*cm, 7*cm])
            info_table_sx.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))

            if ordine.modello.foto:
                try:
                    immagine = Image(ordine.modello.foto.path, width=4*cm, height=4*cm)
                except Exception:
                    immagine = Paragraph("Immagine non trovata", styles['Normal'])
            else:
                immagine = Paragraph("Nessuna foto", styles['Normal'])
            
            header_table = Table([[info_table_sx, immagine]], colWidths=[11*cm, None])
            header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.8*cm))

            elements.append(Paragraph("Riepilogo Paia", styles['h2']))
            taglie_ordinate = sorted(bolla.keys(), key=lambda t: t.numero)
            
            # --- RIGA MODIFICATA ---
            # Usiamo str(t) invece di str(t.numero) per invocare il nostro __str__ personalizzato
            header_row = [Paragraph(str(t), style_bold) for t in taglie_ordinate]
            # --- FINE RIGA MODIFICATA ---
            
            quantita_row = [Paragraph(str(bolla[t]), styles['Normal']) for t in taglie_ordinate]
            quantita_totale_bolla = sum(bolla.values())

            header_row.append(Paragraph("TOTALE", style_bold))
            quantita_row.append(Paragraph(str(quantita_totale_bolla), style_bold))

            table_data = [header_row, quantita_row]
            bolla_table = Table(table_data)
            bolla_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ]))
            elements.append(bolla_table)

            # ... resto della vista invariato ...
            elements.append(Spacer(1, 1*cm))
            elements.append(Paragraph("Distinta Materiali", styles['h2']))
            
            num_righe = ceil(len(componenti_del_modello) / 2)
            colonna_sx_comp = componenti_del_modello[:num_righe]
            colonna_dx_comp = componenti_del_modello[num_righe:]
            
            style_header_mat = ParagraphStyle(name='MatHeader', parent=style_bold, fontSize=9)
            style_body_mat = ParagraphStyle(name='MatBody', parent=styles['Normal'], fontSize=8)

            materiali_sx_data = [[Paragraph("Componente", style_header_mat), Paragraph("Colore", style_header_mat)]]
            for comp in colonna_sx_comp:
                colore = comp.colore.nome if comp.colore else "Non specificato"
                materiali_sx_data.append([Paragraph(comp.nome_componente.nome, style_body_mat), Paragraph(colore, style_body_mat)])
            
            materiali_dx_data = [[Paragraph("Componente", style_header_mat), Paragraph("Colore", style_header_mat)]]
            for comp in colonna_dx_comp:
                colore = comp.colore.nome if comp.colore else "Non specificato"
                materiali_dx_data.append([Paragraph(comp.nome_componente.nome, style_body_mat), Paragraph(colore, style_body_mat)])

            table_sx = Table(materiali_sx_data, colWidths=[6*cm, 6*cm])
            table_dx = Table(materiali_dx_data, colWidths=[6*cm, 6*cm])
            
            common_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.darkgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
            ])
            table_sx.setStyle(common_style)
            table_dx.setStyle(common_style)

            container_table = Table([[table_sx, table_dx]], colWidths=[12.5*cm, 12.5*cm])
            container_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            elements.append(container_table)
            
            if i < total_bolle:
                elements.append(PageBreak())

        doc.build(elements)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bolle_lavoro_ordine_{ordine.pk}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response