from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    numero_telefono = models.CharField(max_length=20, blank=True, null=True)
    indirizzo = models.TextField(blank=True, null=True)
    partita_IVA = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clienti_creati')
    class Meta: verbose_name_plural = "Clienti"; ordering = ['nome']
    def __str__(self): return self.nome
    def get_absolute_url(self): return reverse('cliente_detail', kwargs={'pk': self.pk})

class Colore(models.Model):
    nome = models.CharField(max_length=100)
    valore_hex = models.CharField(max_length=7, default='#FFFFFF')
    descrizione = models.TextField(blank=True, null=True)
    class Meta: verbose_name_plural = "Colori"; ordering = ['nome']
    def __str__(self): return f"{self.nome} ({self.valore_hex})"
    def get_absolute_url(self): return reverse('colore_detail', kwargs={'pk': self.pk})

class Taglia(models.Model):
    numero = models.IntegerField(unique=True, help_text="Es. 38, 39, 40...")
    note = models.TextField(blank=True, null=True)
    class Meta: verbose_name = "Taglia"; verbose_name_plural = "Taglie"; ordering = ['numero']
    def __str__(self): return str(self.numero)
    def get_absolute_url(self): return reverse('taglia_detail', kwargs={'pk': self.pk})

class TipoComponente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True, null=True)
    class Meta: verbose_name_plural = "Tipi Componente"; ordering = ['nome']
    def __str__(self): return self.nome
    def get_absolute_url(self): return reverse('tipocomponente_detail', kwargs={'pk': self.pk})

class Modello(models.Model):
    TIPO_SCARPA_CHOICES = [('CASUAL', 'Casual'), ('ELEGANTE', 'Elegante'), ('SPORTIVA', 'Sportiva'), ('SANDALO', 'Sandalo'), ('STIVALE', 'Stivale'), ('ALTRO', 'Altro')]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='modelli')
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_SCARPA_CHOICES, default='CASUAL')
    foto = models.ImageField(upload_to='modelli/foto/', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modelli_creati')
    class Meta: verbose_name_plural = "Modelli"; ordering = ['nome']; unique_together = ['cliente', 'nome']
    def __str__(self): return f"{self.nome} ({self.get_tipo_display()}) - {self.cliente}"
    def get_absolute_url(self): return reverse('modello_detail', kwargs={'pk': self.pk})
    def duplicate(self, new_name=None):
        new_modello = Modello.objects.create(cliente=self.cliente, nome=new_name or f"{self.nome} (Copia)", tipo=self.tipo, note=self.note, created_by=self.created_by)
        for componente_originale in self.componenti.all():
            new_componente = Componente.objects.create(modello=new_modello, nome_componente=componente_originale.nome_componente, colore=componente_originale.colore, note=componente_originale.note)
            for articolo_originale in componente_originale.articoli.all():
                Articolo.objects.create(componente=new_componente, taglia=articolo_originale.taglia, descrizione_misura=articolo_originale.descrizione_misura)
        return new_modello

class Componente(models.Model):
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='componenti')
    nome_componente = models.ForeignKey(TipoComponente, on_delete=models.PROTECT, help_text="Tipo di componente (es. Suola, Tacco)")
    colore = models.ForeignKey(Colore, on_delete=models.SET_NULL, null=True, blank=True, help_text="Colore specifico per questo componente in questo modello")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: verbose_name_plural = "Componenti del Modello"; ordering = ['nome_componente__nome']
    def __str__(self): return f"{self.nome_componente.nome} per {self.modello.nome}"

class Articolo(models.Model):
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name='articoli')
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE, related_name='articoli')
    descrizione_misura = models.CharField(max_length=200, blank=True, null=True, help_text="Es. 'Lunghezza 28cm, Spessore 5mm'")
    class Meta: verbose_name = "Articolo"; verbose_name_plural = "Articoli"; unique_together = ['componente', 'taglia']
    def __str__(self): return f"{self.componente} per taglia {self.taglia}"

class Ordine(models.Model):
    STATO_ORDINE_CHOICES = [('BOZZA', 'Bozza'), ('CONFERMATO', 'Confermato'), ('IN_PRODUZIONE', 'In produzione'), ('COMPLETATO', 'Completato'), ('ANNULLATO', 'Annullato')]
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='ordini')
    data_ordine = models.DateTimeField(default=timezone.now)
    stato = models.CharField(max_length=20, choices=STATO_ORDINE_CHOICES, default='BOZZA')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ordini_creati')
    class Meta: verbose_name_plural = "Ordini"; ordering = ['-data_ordine']
    def __str__(self): return f"Ordine #{self.id} - {self.modello.nome}"
    def get_absolute_url(self): return reverse('ordine_detail', kwargs={'pk': self.pk})
    @property
    def quantita_totale(self): return sum(d.quantita for d in self.dettagli.all() if d.quantita)
    def get_materiali_necessari(self):
        materiali = {}
        for dettaglio in self.dettagli.all():
            for componente_del_modello in self.modello.componenti.all():
                if Articolo.objects.filter(componente=componente_del_modello, taglia=dettaglio.taglia).exists():
                    key = (componente_del_modello.nome_componente.nome, componente_del_modello.colore)
                    materiali[key] = materiali.get(key, 0) + dettaglio.quantita
        return materiali

class DettaglioOrdine(models.Model):
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='dettagli')
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE)
    quantita = models.IntegerField(validators=[MinValueValidator(1)])
    note = models.TextField(blank=True, null=True)
    class Meta: verbose_name_plural = "Dettagli Ordine"; ordering = ['taglia__numero']; unique_together = ['ordine', 'taglia']
    def __str__(self): return f"{self.quantita}x Taglia {self.taglia} per Ordine #{self.ordine.id}"