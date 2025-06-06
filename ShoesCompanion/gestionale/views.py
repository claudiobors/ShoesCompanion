from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.forms import inlineformset_factory
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
                  DettaglioOrdineForm, ModelloForm, OrdineMainForm,
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
    ArticoloInlineFormSet = inlineformset_factory(Componente, Articolo, form=ArticoloForm, fields=('taglia', 'descrizione_misura'), extra=1, can_delete=True)
    if request.method == 'POST':
        formset = ArticoloInlineFormSet(request.POST, instance=componente, prefix='articoli')
        if formset.is_valid():
            formset.save()
            return redirect('modello_detail', pk=componente.modello.pk)
    else:
        formset = ArticoloInlineFormSet(instance=componente, prefix='articoli')
    return render(request, 'gestionale/componenti/manage_articoli.html', {'formset': formset, 'componente': componente})


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
            data['quantita_form'] = QuantitaPerTagliaForm(self.request.POST)
        else:
            data['quantita_form'] = QuantitaPerTagliaForm()
        return data
    def form_valid(self, form):
        context = self.get_context_data()
        quantita_form = context['quantita_form']
        if quantita_form.is_valid():
            form.instance.created_by = self.request.user
            self.object = form.save()
            for taglia_id, quantita in quantita_form.get_dettagli_data():
                if quantita > 0:
                    DettaglioOrdine.objects.create(ordine=self.object, taglia_id=taglia_id, quantita=quantita)
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.pk})

class OrdineUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Ordine
    form_class = OrdineMainForm
    template_name = 'gestionale/ordini/ordine_form.html'
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        dettagli_esistenti = self.object.dettagli.all()
        if self.request.POST:
            data['quantita_form'] = QuantitaPerTagliaForm(self.request.POST, instance=dettagli_esistenti)
        else:
            data['quantita_form'] = QuantitaPerTagliaForm(instance=dettagli_esistenti)
        return data
    def form_valid(self, form):
        context = self.get_context_data()
        quantita_form = context['quantita_form']
        if quantita_form.is_valid():
            self.object = form.save()
            for taglia_id, quantita in quantita_form.get_dettagli_data():
                if quantita > 0:
                    DettaglioOrdine.objects.update_or_create(ordine=self.object, taglia_id=taglia_id, defaults={'quantita': quantita})
                else:
                    DettaglioOrdine.objects.filter(ordine=self.object, taglia_id=taglia_id).delete()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
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
        if 'ordine' in self.get_context_data():
            form.instance.ordine = self.get_context_data()['ordine']
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.ordine.pk})

class DettaglioOrdineUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = DettaglioOrdine
    form_class = DettaglioOrdineForm
    template_name = 'gestionale/ordini/dettaglioordine_form.html'
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
@login_required
def report_dashboard(request):
    ordini_per_stato = Ordine.objects.values('stato').annotate(count=Count('id'), total=Sum('quantita_totale')).order_by('stato')
    modelli_popolari = Modello.objects.annotate(num_ordini=Count('ordini')).order_by('-num_ordini')[:5]
    clienti_attivi = Cliente.objects.annotate(num_ordini=Count('modelli__ordini')).order_by('-num_ordini')[:5]
    context = {'ordini_per_stato': ordini_per_stato, 'modelli_popolari': modelli_popolari, 'clienti_attivi': clienti_attivi}
    return render(request, 'gestionale/report/dashboard.html', context)

@login_required
def bolla_ordine_pdf(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bolla_ordine_{pk}.pdf"'
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16); p.drawString(100, 800, "BOLLA D'ORDINE")
    p.setFont("Helvetica", 12); p.drawString(100, 780, f"Ordine n. {ordine.id}"); p.drawString(100, 760, f"Cliente: {ordine.modello.cliente.nome}"); p.drawString(100, 740, f"Modello: {ordine.modello.nome}"); p.drawString(100, 720, f"Data: {ordine.data_ordine.strftime('%d/%m/%Y')}")
    p.setFont("Helvetica-Bold", 12); p.drawString(100, 690, "Dettagli Taglie:"); p.drawString(100, 670, "Taglia"); p.drawString(200, 670, "Quantità")
    y = 650
    p.setFont("Helvetica", 10)
    for dettaglio in ordine.dettagli.all().order_by('taglia__numero'):
        p.drawString(100, y, str(dettaglio.taglia)); p.drawString(200, y, str(dettaglio.quantita)); y -= 20
    p.setFont("Helvetica-Bold", 12); p.drawString(100, y-30, f"TOTALE SCARPE: {ordine.quantita_totale}")
    p.showPage(); p.save()
    pdf = buffer.getvalue(); buffer.close(); response.write(pdf)
    return response

@login_required
def scheda_materiali_pdf(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    materiali = ordine.get_materiali_necessari()
    response = HttpResponse(content_type='application/pdf'); response['Content-Disposition'] = f'attachment; filename="scheda_materiali_{pk}.pdf"'
    buffer = BytesIO(); p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16); p.drawString(100, 800, "SCHEDA MATERIALI NECESSARI")
    p.setFont("Helvetica", 12); p.drawString(100, 780, f"Ordine n. {ordine.id}"); p.drawString(100, 760, f"Cliente: {ordine.modello.cliente.nome}"); p.drawString(100, 740, f"Modello: {ordine.modello.nome}"); p.drawString(100, 720, f"Data: {ordine.data_ordine.strftime('%d/%m/%Y')}")
    p.setFont("Helvetica-Bold", 12); p.drawString(100, 690, "Materiali Necessari:"); p.drawString(100, 670, "Componente"); p.drawString(250, 670, "Colore"); p.drawString(400, 670, "Quantità")
    y = 650
    p.setFont("Helvetica", 10)
    for (nome_componente, colore), quantita in materiali.items():
        p.drawString(100, y, nome_componente); p.drawString(250, y, str(colore) if colore else "-"); p.drawString(400, y, str(quantita)); y -= 20
    p.showPage(); p.save()
    pdf = buffer.getvalue(); buffer.close(); response.write(pdf)
    return response

@login_required
def scheda_modello_pdf(request, pk):
    modello = get_object_or_404(Modello, pk=pk)
    response = HttpResponse(content_type='application/pdf'); response['Content-Disposition'] = f'attachment; filename="scheda_modello_{pk}.pdf"'
    buffer = BytesIO(); p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16); p.drawString(100, 800, "SCHEDA MODELLO"); p.setFont("Helvetica", 12); p.drawString(100, 780, f"Modello: {modello.nome}"); p.drawString(100, 760, f"Cliente: {modello.cliente.nome}"); p.drawString(100, 740, f"Tipo: {modello.get_tipo_display()}")
    p.setFont("Helvetica-Bold", 12); p.drawString(100, 710, "Componenti e Misure per Taglia:"); p.drawString(100, 690, "Tipo"); p.drawString(250, 690, "Colore")
    y = 670
    p.setFont("Helvetica-Bold", 10)
    for componente in modello.componenti.all():
        p.drawString(100, y, componente.nome_componente.nome); p.drawString(250, y, str(componente.colore) if componente.colore else "-"); y -= 15
        p.setFont("Helvetica", 9)
        for articolo in componente.articoli.all().order_by('taglia__numero'):
            p.drawString(120, y, f"- Taglia {articolo.taglia}: {articolo.descrizione_misura or 'N/D'}")
            y -= 12
        y -= 5
    if modello.note:
        p.setFont("Helvetica-Bold", 12); p.drawString(100, y-20, "Note Modello:"); p.setFont("Helvetica", 10); p.drawString(100, y-35, modello.note)
    p.showPage(); p.save()
    pdf = buffer.getvalue(); buffer.close(); response.write(pdf)
    return response