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

    class Meta:
        verbose_name_plural = "Clienti"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('cliente_detail', kwargs={'pk': self.pk})


class Colore(models.Model):
    nome = models.CharField(max_length=100)
    valore_hex = models.CharField(max_length=7, default='#FFFFFF')
    descrizione = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Colori"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.valore_hex})"

    def get_absolute_url(self):
        return reverse('colore_detail', kwargs={'pk': self.pk})


class CoppiaMisura(models.Model):
    numero_scarpa = models.IntegerField(validators=[MinValueValidator(1)])
    larghezza = models.DecimalField(max_digits=5, decimal_places=2)
    altezza = models.DecimalField(max_digits=5, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Coppie Misure"
        ordering = ['numero_scarpa']
        unique_together = ['numero_scarpa', 'larghezza', 'altezza']

    def __str__(self):
        return f"Scarpa {self.numero_scarpa} (Larghezza: {self.larghezza}, Altezza: {self.altezza})"

    def get_absolute_url(self):
        return reverse('coppiamisura_detail', kwargs={'pk': self.pk})


class Modello(models.Model):
    TIPO_SCARPA_CHOICES = [
        ('CASUAL', 'Casual'),
        ('ELEGANTE', 'Elegante'),
        ('SPORTIVA', 'Sportiva'),
        ('SANDALO', 'Sandalo'),
        ('STIVALE', 'Stivale'),
        ('ALTRO', 'Altro'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='modelli')
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_SCARPA_CHOICES, default='CASUAL')
    foto = models.ImageField(upload_to='modelli/foto/', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modelli_creati')

    class Meta:
        verbose_name_plural = "Modelli"
        ordering = ['nome']
        unique_together = ['cliente', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()}) - {self.cliente}"

    def get_absolute_url(self):
        return reverse('modello_detail', kwargs={'pk': self.pk})

    def duplicate(self, new_name=None):
        """Duplica il modello con tutti i suoi componenti"""
        new_modello = Modello.objects.create(
            cliente=self.cliente,
            nome=new_name or f"{self.nome} (Copia)",
            tipo=self.tipo,
            note=self.note,
            created_by=self.created_by
        )
        
        # Copia i componenti
        for componente in self.componenti.all():
            new_componente = Componente.objects.create(
                modello=new_modello,
                nome=componente.nome,
                colore=componente.colore,
                note=componente.note
            )
            new_componente.coppie_misure.set(componente.coppie_misure.all())
        
        return new_modello


class Componente(models.Model):
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='componenti')
    nome = models.CharField(max_length=200)
    colore = models.ForeignKey(Colore, on_delete=models.SET_NULL, null=True, blank=True)
    coppie_misure = models.ManyToManyField(CoppiaMisura, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Componenti"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.colore}) - {self.modello}"

    def get_absolute_url(self):
        return reverse('componente_detail', kwargs={'pk': self.pk})


class Ordine(models.Model):
    STATO_ORDINE_CHOICES = [
        ('BOZZA', 'Bozza'),
        ('CONFERMATO', 'Confermato'),
        ('IN_PRODUZIONE', 'In produzione'),
        ('COMPLETATO', 'Completato'),
        ('ANNULLATO', 'Annullato'),
    ]

    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='ordini')
    data_ordine = models.DateTimeField(default=timezone.now)
    stato = models.CharField(max_length=20, choices=STATO_ORDINE_CHOICES, default='BOZZA')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ordini_creati')

    class Meta:
        verbose_name_plural = "Ordini"
        ordering = ['-data_ordine']

    def __str__(self):
        return f"Ordine #{self.id} - {self.modello} ({self.get_stato_display()})"

    def get_absolute_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.pk})

    @property
    def quantita_totale(self):
        return sum(dettaglio.quantita for dettaglio in self.dettagli.all())

    def get_materiali_necessari(self):
        """Calcola i materiali necessari per questo ordine"""
        materiali = {}
        
        for dettaglio in self.dettagli.all():
            coppia_misura = dettaglio.coppia_misura
            quantita = dettaglio.quantita
            
            for componente in self.modello.componenti.all():
                if coppia_misura in componente.coppie_misure.all() or not componente.coppie_misure.exists():
                    key = (componente.nome, componente.colore)
                    materiali[key] = materiali.get(key, 0) + quantita
        
        return materiali


class DettaglioOrdine(models.Model):
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='dettagli')
    coppia_misura = models.ForeignKey(CoppiaMisura, on_delete=models.CASCADE)
    quantita = models.IntegerField(validators=[MinValueValidator(1)])
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Dettagli Ordine"
        ordering = ['coppia_misura__numero_scarpa']
        unique_together = ['ordine', 'coppia_misura']

    def __str__(self):
        return f"{self.quantita}x {self.coppia_misura} per {self.ordine}"

    def get_absolute_url(self):
        return reverse('dettaglioordine_detail', kwargs={'pk': self.pk})