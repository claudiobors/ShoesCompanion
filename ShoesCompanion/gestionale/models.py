from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

# --- MODELLI DI BASE ---
class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    # ... (il resto del modello Cliente è invariato)
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
    # ... (il resto del modello Colore è invariato)
    valore_hex = models.CharField(max_length=7, default='#FFFFFF')
    descrizione = models.TextField(blank=True, null=True)
    class Meta: verbose_name_plural = "Colori"; ordering = ['nome']
    def __str__(self): return f"{self.nome} ({self.valore_hex})"
    def get_absolute_url(self): return reverse('colore_detail', kwargs={'pk': self.pk})

class Taglia(models.Model):
    numero = models.IntegerField(unique=True, help_text="Es. 38, 39, 40...")
    # ... (il resto del modello Taglia è invariato)
    note = models.TextField(blank=True, null=True)
    class Meta: verbose_name = "Taglia"; verbose_name_plural = "Taglie"; ordering = ['numero']
    def __str__(self): return str(self.numero)
    def get_absolute_url(self): return reverse('taglia_detail', kwargs={'pk': self.pk})

class TipoComponente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    # ... (il resto del modello TipoComponente è invariato)
    descrizione = models.TextField(blank=True, null=True)
    class Meta: verbose_name_plural = "Tipi Componente"; ordering = ['nome']
    def __str__(self): return self.nome
    def get_absolute_url(self): return reverse('tipocomponente_detail', kwargs={'pk': self.pk})

# --- MODELLI PRINCIPALI ---
class Modello(models.Model):
    # ... (codice del modello quasi invariato, ma aggiorniamo il metodo duplicate)
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
        """Duplica il modello, i suoi componenti e le loro misure specifiche (Articoli)."""
        new_modello = Modello.objects.create(cliente=self.cliente, nome=new_name or f"{self.nome} (Copia)", tipo=self.tipo, note=self.note, created_by=self.created_by)
        for componente_originale in self.componenti.all():
            new_componente = Componente.objects.create(modello=new_modello, nome_componente=componente_originale.nome_componente, colore=componente_originale.colore, note=componente_originale.note)
            for articolo_originale in componente_originale.articoli.all():
                # Copia le nuove misure specifiche
                Articolo.objects.create(
                    componente=new_componente,
                    taglia=articolo_originale.taglia,
                    altezza=articolo_originale.altezza,
                    larghezza=articolo_originale.larghezza
                )
        return new_modello

class Componente(models.Model):
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='componenti')
    # ... (il resto del modello Componente è invariato)
    nome_componente = models.ForeignKey(TipoComponente, on_delete=models.PROTECT, help_text="Tipo di componente (es. Suola, Tacco)")
    colore = models.ForeignKey(Colore, on_delete=models.SET_NULL, null=True, blank=True, help_text="Colore specifico per questo componente in questo modello")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: verbose_name_plural = "Componenti del Modello"; ordering = ['nome_componente__nome']
    def __str__(self): return f"{self.nome_componente.nome} per {self.modello.nome}"

# --- MODELLO Articolo MODIFICATO ---
class Articolo(models.Model):
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name='articoli')
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE, related_name='articoli')
    
    # CAMPI MODIFICATI: da un campo di testo a due campi numerici
    altezza = models.DecimalField(max_digits=6, decimal_places=2, help_text="Altezza del componente in mm per questa taglia")
    larghezza = models.DecimalField(max_digits=6, decimal_places=2, help_text="Larghezza del componente in mm per questa taglia")
    
    class Meta:
        verbose_name = "Articolo (Misura Componente per Taglia)"
        verbose_name_plural = "Articoli (Misure Componenti per Taglia)"
        unique_together = ['componente', 'taglia']

    def __str__(self):
        return f"{self.componente} per taglia {self.taglia} (H: {self.altezza}mm, L: {self.larghezza}mm)"


# --- MODELLI ORDINE (invariati, ma si baseranno sulla nuova struttura) ---
class Ordine(models.Model):
    # ... (il resto del modello Ordine è invariato)
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
        materiali = {};
        for dettaglio in self.dettagli.all():
            for componente_del_modello in self.modello.componenti.all():
                if Articolo.objects.filter(componente=componente_del_modello, taglia=dettaglio.taglia).exists():
                    key = (componente_del_modello.nome_componente.nome, componente_del_modello.colore); materiali[key] = materiali.get(key, 0) + dettaglio.quantita
        return materiali
    

    def get_materiali_necessari(self):
        """
        Calcola la somma delle misure (altezza e larghezza) per ogni tipo di
        componente/colore necessario per completare l'ordine.
        """
        # Il dizionario finale conterrà:
        # { 
        #   (nome_tipo_componente, colore_obj): {
        #       'tot_altezza': X, 
        #       'tot_larghezza': Y,
        #       'unita_prodotte': Z
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
                
                if articolo:
                    # Se l'articolo esiste, ho le sue misure
                    key = (componente.nome_componente.nome, componente.colore)
                    
                    # Inizializzo il dizionario per questo materiale se non l'ho ancora incontrato
                    misure = materiali.setdefault(key, {
                        'tot_altezza': 0, 
                        'tot_larghezza': 0,
                        'unita_prodotte': 0
                    })
                    
                    # Sommo le misure totali per questa riga di dettaglio
                    misure['tot_altezza'] += articolo.altezza * quantita_per_taglia
                    misure['tot_larghezza'] += articolo.larghezza * quantita_per_taglia
                    misure['unita_prodotte'] += quantita_per_taglia

        return materiali

class DettaglioOrdine(models.Model):
    # ... (il resto del modello DettaglioOrdine è invariato)
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='dettagli')
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE)
    quantita = models.IntegerField(validators=[MinValueValidator(1)])
    note = models.TextField(blank=True, null=True)
    class Meta: verbose_name_plural = "Dettagli Ordine"; ordering = ['taglia__numero']; unique_together = ['ordine', 'taglia']
    def __str__(self): return f"{self.quantita}x Taglia {self.taglia} per Ordine #{self.ordine.id}"