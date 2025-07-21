from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal

# Costante di conversione
SQ_FOOT_TO_SQ_METER = Decimal('0.092903')
SQ_METER_TO_SQ_FOOT = Decimal('1') / SQ_FOOT_TO_SQ_METER

# --- MODELLI DI BASE ---
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

class Taglia(models.Model):
    numero = models.DecimalField(max_digits=5, decimal_places=2, unique=True, help_text="Es. 38, 39, 40...")
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Taglia"
        verbose_name_plural = "Taglie"
        ordering = ['numero']

    def __str__(self):
        return str(self.numero)

    def get_absolute_url(self):
        return reverse('taglia_detail', kwargs={'pk': self.pk})

class TipoComponente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Tipi Componente"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('tipocomponente_detail', kwargs={'pk': self.pk})

# --- MODELLI PRINCIPALI ---
class Modello(models.Model):
    TIPO_SCARPA_CHOICES = [
        ('CASUAL', 'Casual'), ('ELEGANTE', 'Elegante'), ('SPORTIVA', 'Sportiva'),
        ('SANDALO', 'Sandalo'), ('STIVALE', 'Stivale'), ('ALTRO', 'Altro')
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

    
    def duplicate(self, new_name=None, created_by=None): # 1. Aggiungi l'argomento 'created_by'
        """Duplica il modello, i suoi componenti e le loro misure specifiche (Articoli)."""
        new_modello = Modello.objects.create(
            cliente=self.cliente,
            nome=new_name or f"{self.nome} (Copia)",
            tipo=self.tipo,
            note=self.note,
            created_by=created_by or self.created_by # 2. Usa il nuovo argomento qui
        )
        for componente_originale in self.componenti.all():
            new_componente = Componente.objects.create(
                modello=new_modello,
                nome_componente=componente_originale.nome_componente,
                colore=componente_originale.colore,
                note=componente_originale.note
            )
            for articolo_originale in componente_originale.articoli.all():
                Articolo.objects.create(
                    componente=new_componente,
                    taglia=articolo_originale.taglia,
                    superficie_mq=articolo_originale.superficie_mq,
                    superficie_piedi_quadri=articolo_originale.superficie_piedi_quadri
                )
        return new_modello

class Componente(models.Model):
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='componenti')
    nome_componente = models.ForeignKey(TipoComponente, on_delete=models.PROTECT, help_text="Tipo di componente (es. Suola, Tacco)")
    colore = models.ForeignKey(Colore, on_delete=models.SET_NULL, null=True, blank=True, help_text="Colore specifico per questo componente in questo modello")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Componenti del Modello"
        ordering = ['nome_componente__nome']

    def __str__(self):
        return f"{self.nome_componente.nome} per {self.modello.nome}"

# --- MODELLO Articolo MODIFICATO ---
class Articolo(models.Model):
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name='articoli')
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE, related_name='articoli')

    # CAMPI MODIFICATI: da altezza e larghezza a superficie in MQ e Piedi Quadri
    superficie_mq = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True,
        help_text="Superficie del componente in metri quadrati per questa taglia"
    )
    superficie_piedi_quadri = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True,
        help_text="Superficie del componente in piedi quadrati per questa taglia"
    )

    class Meta:
        verbose_name = "Articolo (Misura Componente per Taglia)"
        verbose_name_plural = "Articoli (Misure Componenti per Taglia)"
        unique_together = ['componente', 'taglia']

    def __str__(self):
        mq_str = f"{self.superficie_mq:.2f} MQ" if self.superficie_mq is not None else "N/A"
        piedi_str = f"{self.superficie_piedi_quadri:.2f} Pq" if self.superficie_piedi_quadri is not None else "N/A"
        return f"{self.componente} per taglia {self.taglia} (Sup: {mq_str}, {piedi_str})"

    def clean(self):
        # Assicurati che almeno uno dei campi di superficie sia compilato
        if self.superficie_mq is None and self.superficie_piedi_quadri is None:
            from django.core.exceptions import ValidationError
            raise ValidationError("Devi specificare almeno la superficie in Metri Quadrati o Piedi Quadrati.")

    def save(self, *args, **kwargs):
        # Converti e riempi il campo mancante prima di salvare
        if self.superficie_mq is not None and self.superficie_piedi_quadri is None:
            self.superficie_piedi_quadri = self.superficie_mq * SQ_METER_TO_SQ_FOOT
        elif self.superficie_piedi_quadri is not None and self.superficie_mq is None:
            self.superficie_mq = self.superficie_piedi_quadri * SQ_FOOT_TO_SQ_METER
        super().save(*args, **kwargs)


# --- MODELLI ORDINE (con get_materiali_necessari aggiornato) ---
class Ordine(models.Model):
    STATO_ORDINE_CHOICES = [
        ('BOZZA', 'Bozza'), ('CONFERMATO', 'Confermato'),
        ('IN_PRODUZIONE', 'In produzione'), ('COMPLETATO', 'Completato'), ('ANNULLATO', 'Annullato')
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
        return f"Ordine #{self.id} - {self.modello.nome}"

    def get_absolute_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.pk})

    @property
    def quantita_totale(self):
        return sum(d.quantita for d in self.dettagli.all() if d.quantita)

    def get_materiali_necessari(self):
        """
        Calcola la somma delle superfici (in MQ e Piedi Quadrati) per ogni tipo di
        componente/colore necessario per completare l'ordine.
        """
        # Il dizionario finale conterrà:
        # {
        #   (nome_tipo_componente, colore_obj): {
        #     'tot_superficie_mq': X,
        #     'tot_superficie_piedi_quadri': Y,
        #     'unita_prodotte': Z
        #   }
        # }
        materiali = {}

        # Pre-carico i dati correlati per ottimizzare le query al database
        dettagli_ordine = self.dettagli.select_related('taglia').all()
        componenti_modello = self.modello.componenti.select_related('nome_componente', 'colore').all()
        articoli_modello = Articolo.objects.filter(componente__modello=self.modello).select_related('taglia', 'componente')

        # Creo una mappa per un accesso super-veloce agli articoli, senza fare query in loop
        # La chiave è (ID_componente, ID_taglia) e il valore è l'oggetto Articolo
        articoli_map = {(a.componente_id, a.taglia_id): a for a in articoli_modello}

        for dettaglio in dettagli_ordine:
            quantita_per_taglia = dettaglio.quantita

            for componente in componenti_modello:
                # Cerco l'articolo corrispondente nella mappa
                articolo = articoli_map.get((componente.id, dettaglio.taglia_id))

                if articolo and (articolo.superficie_mq is not None or articolo.superficie_piedi_quadri is not None):
                    # Se l'articolo esiste e ha misure di superficie
                    key = (componente.nome_componente.nome, componente.colore)

                    # Inizializzo il dizionario per questo materiale se non l'ho ancora incontrato
                    misure = materiali.setdefault(key, {
                        'tot_superficie_mq': Decimal('0.0'),
                        'tot_superficie_piedi_quadri': Decimal('0.0'),
                        'unita_prodotte': 0
                    })

                    # Sommo le misure totali per questa riga di dettaglio
                    if articolo.superficie_mq is not None:
                        misure['tot_superficie_mq'] += articolo.superficie_mq * quantita_per_taglia
                    if articolo.superficie_piedi_quadri is not None:
                        misure['tot_superficie_piedi_quadri'] += articolo.superficie_piedi_quadri * quantita_per_taglia
                    
                    misure['unita_prodotte'] += quantita_per_taglia

        return materiali

class DettaglioOrdine(models.Model):
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='dettagli')
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE)
    quantita = models.IntegerField(validators=[MinValueValidator(1)])
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Dettagli Ordine"
        ordering = ['taglia__numero']
        unique_together = ['ordine', 'taglia']

    def __str__(self):
        return f"{self.quantita}x Taglia {self.taglia} per Ordine #{self.ordine.id}"
    
class StrutturaModello(models.Model):
        nome = models.CharField(max_length=100, unique=True, help_text="Es. Décolleté Base, Stivale Texano, Sandalo Gioiello")
        tipi_componente = models.ManyToManyField(TipoComponente, help_text="Seleziona i componenti base per questo tipo di struttura.")

        class Meta:
            verbose_name = "Struttura Modello"
            verbose_name_plural = "Strutture Modello"
            ordering = ['nome']

        def __str__(self):
            return self.nome