from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Sum
from reportlab.pdfgen import canvas
from io import BytesIO

from .models import Cliente, Modello, Componente, Colore, CoppiaMisura, Ordine, DettaglioOrdine
from .forms import (
    ClienteForm, ModelloForm, ComponenteForm, ColoreForm, 
    CoppiaMisuraForm, OrdineForm, DettaglioOrdineForm
)
from .tables import (
    ClienteTable, ModelloTable, ComponenteTable, ColoreTable, 
    CoppiaMisuraTable, OrdineTable
)
from .filters import (
    ClienteFilter, ModelloFilter, ComponenteFilter, ColoreFilter, 
    CoppiaMisuraFilter, OrdineFilter
)


from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from gestionale.models import Cliente, Modello, Ordine, DettaglioOrdine

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Statistiche principali
    context = {
        'clienti_count': Cliente.objects.count(),
        'modelli_count': Modello.objects.count(),
        'ordini_attivi_count': Ordine.objects.exclude(
            stato__in=['COMPLETATO', 'ANNULLATO']
        ).count(),
        'scarpe_da_produrre': DettaglioOrdine.objects.filter(
            ordine__stato='CONFERMATO'
        ).aggregate(Sum('quantita'))['quantita__sum'] or 0,
        
        # Ordini recenti (ultimi 5)
        'ordini_recenti': Ordine.objects.select_related(
            'modello', 'modello__cliente'
        ).order_by('-data_ordine')[:5],
        
        # Dati per il grafico
        'stati_ordine': Ordine.objects.values('stato').annotate(
            count=Count('stato')
        ).order_by('stato'),
    }
    
    # Converti i dati del grafico in un formato più semplice
    stati_data = {item['stato']: item['count'] for item in context['stati_ordine']}
    context['stati_ordine'] = {
        'BOZZA': stati_data.get('BOZZA', 0),
        'CONFERMATO': stati_data.get('CONFERMATO', 0),
        'IN_PRODUZIONE': stati_data.get('IN_PRODUZIONE', 0),
        'COMPLETATO': stati_data.get('COMPLETATO', 0),
        'ANNULLATO': stati_data.get('ANNULLATO', 0),
    }
    
    return render(request, 'gestionale/home.html', context)


# Clienti Views
class ClienteListView(LoginRequiredMixin, generic.ListView):
    model = Cliente
    template_name = 'gestionale/clienti/cliente_list.html'
    context_object_name = 'clienti'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = ClienteFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = ClienteTable(self.get_queryset())
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
    success_url = reverse_lazy('cliente_list')


class ClienteDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Cliente
    template_name = 'gestionale/clienti/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')


# Modelli Views
class ModelloListView(LoginRequiredMixin, generic.ListView):
    model = Modello
    template_name = 'gestionale/modelli/modello_list.html'
    context_object_name = 'modelli'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = ModelloFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = ModelloTable(self.get_queryset())
        return context


class ModelloDetailView(LoginRequiredMixin, generic.DetailView):
    model = Modello
    template_name = 'gestionale/modelli/modello_detail.html'


class ModelloCreateView(LoginRequiredMixin, generic.CreateView):
    model = Modello
    form_class = ModelloForm
    template_name = 'gestionale/modelli/modello_form.html'
    success_url = reverse_lazy('modello_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ModelloUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Modello
    form_class = ModelloForm
    template_name = 'gestionale/modelli/modello_form.html'
    success_url = reverse_lazy('modello_list')


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


# Componenti Views
class ComponenteListView(LoginRequiredMixin, generic.ListView):
    model = Componente
    template_name = 'gestionale/componenti/componente_list.html'
    context_object_name = 'componenti'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = ComponenteFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = ComponenteTable(self.get_queryset())
        return context


class ComponenteDetailView(LoginRequiredMixin, generic.DetailView):
    model = Componente
    template_name = 'gestionale/componenti/componente_detail.html'


class ComponenteCreateView(LoginRequiredMixin, generic.CreateView):
    model = Componente
    form_class = ComponenteForm
    template_name = 'gestionale/componenti/componente_form.html'

    def get_success_url(self):
        return reverse('modello_detail', kwargs={'pk': self.object.modello.pk})

    def get_initial(self):
        initial = super().get_initial()
        if 'modello_id' in self.kwargs:
            initial['modello'] = get_object_or_404(Modello, pk=self.kwargs['modello_id'])
        return initial


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


# Ordini Views
class OrdineListView(LoginRequiredMixin, generic.ListView):
    model = Ordine
    template_name = 'gestionale/ordini/ordine_list.html'
    context_object_name = 'ordini'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = OrdineFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = OrdineTable(self.get_queryset())
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
    form_class = OrdineForm
    template_name = 'gestionale/ordini/ordine_form.html'

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        if 'modello_id' in self.kwargs:
            initial['modello'] = get_object_or_404(Modello, pk=self.kwargs['modello_id'])
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class OrdineUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Ordine
    form_class = OrdineForm
    template_name = 'gestionale/ordini/ordine_form.html'

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.pk})


class OrdineDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Ordine
    template_name = 'gestionale/ordini/ordine_confirm_delete.html'
    success_url = reverse_lazy('ordine_list')


@login_required
def ordine_conferma(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    if ordine.stato == 'BOZZA':
        ordine.stato = 'CONFERMATO'
        ordine.save()
    return redirect('ordine_detail', pk=ordine.pk)


@login_required
def ordine_annulla(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    if ordine.stato in ['BOZZA', 'CONFERMATO']:
        ordine.stato = 'ANNULLATO'
        ordine.save()
    return redirect('ordine_detail', pk=ordine.pk)


# DettaglioOrdine Views
class DettaglioOrdineCreateView(LoginRequiredMixin, generic.CreateView):
    model = DettaglioOrdine
    form_class = DettaglioOrdineForm
    template_name = 'gestionale/ordini/dettaglioordine_form.html'

    def get_success_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.object.ordine.pk})

    def get_initial(self):
        initial = super().get_initial()
        if 'ordine_id' in self.kwargs:
            initial['ordine'] = get_object_or_404(Ordine, pk=self.kwargs['ordine_id'])
        return initial


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


# Report Views
@login_required
def bolla_ordine_pdf(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bolla_ordine_{pk}.pdf"'
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Intestazione
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "BOLLA D'ORDINE")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Ordine n. {ordine.id}")
    p.drawString(100, 760, f"Cliente: {ordine.modello.cliente.nome}")
    p.drawString(100, 740, f"Modello: {ordine.modello.nome}")
    p.drawString(100, 720, f"Data: {ordine.data_ordine.strftime('%d/%m/%Y')}")
    
    # Dettagli ordine
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 690, "Dettagli Taglie:")
    p.drawString(100, 670, "Taglia")
    p.drawString(200, 670, "Quantità")
    
    y = 650
    p.setFont("Helvetica", 10)
    for dettaglio in ordine.dettagli.all().order_by('coppia_misura__numero_scarpa'):
        p.drawString(100, y, str(dettaglio.coppia_misura))
        p.drawString(200, y, str(dettaglio.quantita))
        y -= 20
    
    # Totale
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y-30, f"TOTALE SCARPE: {ordine.quantita_totale}")
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def scheda_materiali_pdf(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    materiali = ordine.get_materiali_necessari()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="scheda_materiali_{pk}.pdf"'
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Intestazione
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "SCHEDA MATERIALI NECESSARI")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Ordine n. {ordine.id}")
    p.drawString(100, 760, f"Cliente: {ordine.modello.cliente.nome}")
    p.drawString(100, 740, f"Modello: {ordine.modello.nome}")
    p.drawString(100, 720, f"Data: {ordine.data_ordine.strftime('%d/%m/%Y')}")
    
    # Materiali
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 690, "Materiali Necessari:")
    p.drawString(100, 670, "Componente")
    p.drawString(200, 670, "Colore")
    p.drawString(300, 670, "Quantità")
    
    y = 650
    p.setFont("Helvetica", 10)
    for (nome, colore), quantita in materiali.items():
        p.drawString(100, y, nome)
        p.drawString(200, y, str(colore))
        p.drawString(300, y, str(quantita))
        y -= 20
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def scheda_modello_pdf(request, pk):
    modello = get_object_or_404(Modello, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="scheda_modello_{pk}.pdf"'
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Intestazione
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "SCHEDA MODELLO")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Modello: {modello.nome}")
    p.drawString(100, 760, f"Cliente: {modello.cliente.nome}")
    p.drawString(100, 740, f"Tipo: {modello.get_tipo_display()}")
    
    # Componenti
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 710, "Componenti:")
    p.drawString(100, 690, "Nome")
    p.drawString(200, 690, "Colore")
    p.drawString(300, 690, "Taglie")
    
    y = 670
    p.setFont("Helvetica", 10)
    for componente in modello.componenti.all():
        p.drawString(100, y, componente.nome)
        p.drawString(200, y, str(componente.colore))
        
        taglie = ", ".join([str(cm) for cm in componente.coppie_misure.all()])
        if not taglie:
            taglie = "Tutte"
        p.drawString(300, y, taglie)
        
        y -= 20
    
    # Note
    if modello.note:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y-30, "Note:")
        p.setFont("Helvetica", 10)
        p.drawString(100, y-50, modello.note)
    
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

class ColoreListView(LoginRequiredMixin, generic.ListView):
    model = Colore
    template_name = 'gestionale/colori/colore_list.html'
    context_object_name = 'colori'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = ColoreFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = ColoreTable(self.get_queryset())
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
    success_url = reverse_lazy('colore_list')


class ColoreDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Colore
    template_name = 'gestionale/colori/colore_confirm_delete.html'
    success_url = reverse_lazy('colore_list')

class ColoreListView(LoginRequiredMixin, generic.ListView):
    model = Colore
    template_name = 'gestionale/colori/colore_list.html'
    context_object_name = 'colori'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = ColoreFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = ColoreTable(self.get_queryset())
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
    success_url = reverse_lazy('colore_list')


class ColoreDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Colore
    template_name = 'gestionale/colori/colore_confirm_delete.html'
    success_url = reverse_lazy('colore_list')

class CoppiaMisuraListView(LoginRequiredMixin, generic.ListView):
    model = CoppiaMisura
    template_name = 'gestionale/coppiemisure/coppiamisura_list.html'
    context_object_name = 'coppiemisure'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter = CoppiaMisuraFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter
        context['table'] = CoppiaMisuraTable(self.get_queryset())
        return context


class CoppiaMisuraDetailView(LoginRequiredMixin, generic.DetailView):
    model = CoppiaMisura
    template_name = 'gestionale/coppiemisure/coppiamisura_detail.html'


class CoppiaMisuraCreateView(LoginRequiredMixin, generic.CreateView):
    model = CoppiaMisura
    form_class = CoppiaMisuraForm
    template_name = 'gestionale/coppiemisure/coppiamisura_form.html'
    success_url = reverse_lazy('coppiamisura_list')


class CoppiaMisuraUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = CoppiaMisura
    form_class = CoppiaMisuraForm
    template_name = 'gestionale/coppiemisure/coppiamisura_form.html'
    success_url = reverse_lazy('coppiamisura_list')


class CoppiaMisuraDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = CoppiaMisura
    template_name = 'gestionale/coppiemisure/coppiamisura_confirm_delete.html'
    success_url = reverse_lazy('coppiamisura_list')

def report_dashboard(request):
    # Statistiche ordini per stato
    ordini_per_stato = Ordine.objects.values('stato').annotate(
        count=Count('id'),
        total=Sum('quantita_totale')
    ).order_by('stato')

    # Top 5 modelli più ordinati
    modelli_popolari = Modello.objects.annotate(
        num_ordini=Count('ordini')
    ).order_by('-num_ordini')[:5]

    # Clienti con più ordini
    clienti_attivi = Cliente.objects.annotate(
        num_ordini=Count('modelli__ordini')
    ).order_by('-num_ordini')[:5]

    context = {
        'ordini_per_stato': ordini_per_stato,
        'modelli_popolari': modelli_popolari,
        'clienti_attivi': clienti_attivi,
    }
    return render(request, 'gestionale/report/dashboard.html', context)