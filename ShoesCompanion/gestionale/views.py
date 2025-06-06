from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.forms import inlineformset_factory
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic

from io import BytesIO
from reportlab.pdfgen import canvas

from .filters import (ClienteFilter, ColoreFilter, ComponenteFilter,
                    ModelloFilter, OrdineFilter, TagliaFilter,
                    TipoComponenteFilter)
from .forms import (ArticoloForm, ClienteForm, ColoreForm, ComponenteForm,
                  DettaglioOrdineForm, ModelloForm, OrdineMainForm,DettaglioOrdineFormSet,
                  QuantitaPerTagliaForm, TagliaForm, TipoComponenteForm)
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

class ModelloCreateView(LoginRequiredMixin, generic.CreateView):
    model = Modello
    form_class = ModelloForm
    template_name = 'gestionale/modelli/modello_form.html'
    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('cliente'):
            initial['cliente'] = get_object_or_404(Cliente, pk=self.request.GET.get('cliente'))
        return initial
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
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
    
    # Use the correct fields: 'altezza' and 'larghezza'
    ArticoloInlineFormSet = inlineformset_factory(
        Componente, 
        Articolo, 
        form=ArticoloForm, 
        fields=('taglia', 'altezza', 'larghezza'),  # <-- CORRECTED LINE
        extra=1, 
        can_delete=True
    )

    if request.method == 'POST':
        formset = ArticoloInlineFormSet(request.POST, instance=componente, prefix='articoli')
        if formset.is_valid():
            formset.save()
            return redirect('modello_detail', pk=componente.modello.pk)
    else:
        formset = ArticoloInlineFormSet(instance=componente, prefix='articoli')
        
    context = {'formset': formset, 'componente': componente}
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

class OrdineCreateView(LoginRequiredMixin, generic.CreateView):
    model = Ordine
    form_class = OrdineMainForm
    template_name = 'gestionale/ordini/ordine_form.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['dettagli_formset'] = DettaglioOrdineFormSet(self.request.POST, prefix='dettagli')
        else:
            data['dettagli_formset'] = DettaglioOrdineFormSet(prefix='dettagli')
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        dettagli_formset = context['dettagli_formset']

        if not dettagli_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        # --- Logica Personalizzata per Sommare le Quantità ---
        taglie_aggregate = {}
        for dettaglio_form in dettagli_formset:
            if dettaglio_form.is_valid() and not dettaglio_form.cleaned_data.get('DELETE', False):
                taglia = dettaglio_form.cleaned_data.get('taglia')
                quantita = dettaglio_form.cleaned_data.get('quantita')
                if taglia and quantita:
                    taglie_aggregate[taglia] = taglie_aggregate.get(taglia, 0) + quantita
        
        if not taglie_aggregate:
            # Se non è stata inserita nessuna riga valida, mostra un errore
            form.add_error(None, "È necessario inserire almeno una riga di dettaglio con taglia e quantità.")
            return self.render_to_response(self.get_context_data(form=form))

        form.instance.created_by = self.request.user
        self.object = form.save()

        for taglia, quantita_totale in taglie_aggregate.items():
            DettaglioOrdine.objects.create(ordine=self.object, taglia=taglia, quantita=quantita_totale)
            
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.pk})

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

@login_required
def report_dashboard(request):
    """
    Mostra una dashboard con analisi avanzate, incluso il calcolo
    totale dei materiali necessari per gli ordini attivi.
    """
    
    # --- 1. Calcolo Aggregato dei Materiali da Ordinare ---
    ordini_attivi = Ordine.objects.exclude(stato__in=['COMPLETATO', 'ANNULLATO'])
    
    materiali_da_ordinare = {}

    for ordine in ordini_attivi.prefetch_related('dettagli__taglia', 'modello__componenti__nome_componente', 'modello__componenti__colore'):
        materiali_per_ordine = ordine.get_materiali_necessari()
        
        for key, misure in materiali_per_ordine.items():
            master_entry = materiali_da_ordinare.setdefault(key, {'tot_altezza': 0, 'tot_larghezza': 0, 'unita_prodotte': 0})
            master_entry['tot_altezza'] += misure.get('tot_altezza', 0)
            master_entry['tot_larghezza'] += misure.get('tot_larghezza', 0)
            master_entry['unita_prodotte'] += misure.get('unita_prodotte', 0)

    # --- 2. Statistiche Ordini per Stato ---
    ordini_per_stato_qs = Ordine.objects.values('stato').annotate(
        count=Count('id'),
        total_pairs=Sum('dettagli__quantita') 
    ).order_by('stato')
    ordini_per_stato_list = list(ordini_per_stato_qs)
    
    # --- 3. Altre Statistiche ---
    modelli_popolari = Modello.objects.annotate(num_ordini=Count('ordini')).order_by('-num_ordini')[:5]
    clienti_attivi = Cliente.objects.annotate(num_ordini=Count('modelli__ordini')).order_by('-num_ordini')[:5]

    context = {
        'materiali_da_ordinare': materiali_da_ordinare,
        'ordini_per_stato': ordini_per_stato_list,
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
    data_materiali = [["Componente", "Colore", "Unità", "Altezza Tot. (mm)", "Larghezza Tot. (mm)"]]
    
    for key, misure in materiali.items():
        nome_componente, colore = key
        data_materiali.append([
            Paragraph(nome_componente, styles['BodyText']),
            Paragraph(colore.nome if colore else "-", styles['BodyText']),
            misure['unita_prodotte'],
            f"{misure['tot_altezza']:.2f}",
            f"{misure['tot_larghezza']:.2f}",
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
            data_articoli = [["Taglia", "Altezza (mm)", "Larghezza (mm)"]]
            for articolo in articoli:
                data_articoli.append([str(articolo.taglia), f"{articolo.altezza:.2f}", f"{articolo.larghezza:.2f}"])
            
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