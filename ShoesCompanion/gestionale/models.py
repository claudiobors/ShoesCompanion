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
    """
    Rappresenta una misura specifica (es. taglia 42, larghezza specifica per un tacco).
    Questa non è più legata direttamente alla scarpa nel suo complesso, ma a un componente specifico
    all'interno di un modello di scarpa.
    """
    descrizione_misura = models.CharField(max_length=100, help_text="Es. 'Taglia 42', 'Lunghezza 10cm per tacco'")
    # Puoi aggiungere campi più specifici se necessario, es:
    # lunghezza = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    # larghezza = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    # altezza = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    numero_scarpa_riferimento = models.IntegerField(validators=[MinValueValidator(1)], blank=True, null=True, help_text="Numero scarpa a cui questa misura si riferisce (se applicabile)")
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Misure Specifiche Componenti"
        ordering = ['descrizione_misura']

    def __str__(self):
        if self.numero_scarpa_riferimento:
            return f"{self.descrizione_misura} (Rif. Scarpa: {self.numero_scarpa_riferimento})"
        return self.descrizione_misura

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
        """Duplica il modello con tutti i suoi componenti e le relative misure."""
        new_modello = Modello.objects.create(
            cliente=self.cliente,
            nome=new_name or f"{self.nome} (Copia {timezone.now().strftime('%Y%m%d%H%M%S')})",
            tipo=self.tipo,
            note=self.note,
            created_by=self.created_by
        )

        for componente_originale in self.componenti.all():
            # Crea il nuovo componente
            new_componente = Componente.objects.create(
                modello=new_modello,
                nome_componente=componente_originale.nome_componente, # Assumendo che hai un model TipoComponente o un CharField
                colore=componente_originale.colore,
                note=componente_originale.note
            )
            # Copia le associazioni MisuraComponente
            for misura_comp_originale in componente_originale.misure_associate.all():
                MisuraComponente.objects.create(
                    componente=new_componente,
                    coppia_misura=misura_comp_originale.coppia_misura,
                    quantita_necessaria=misura_comp_originale.quantita_necessaria # Se hai un campo del genere
                )
        return new_modello

class TipoComponente(models.Model):
    """ Modello per definire i tipi di componente (es. Suola, Tacco, Tomaia) """
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Tipi Componente"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Componente(models.Model):
    """
    Rappresenta un singolo componente di un modello di scarpa (es. la suola del ModelloX).
    Ogni componente ha un tipo (es. 'Suola'), un colore e delle misure specifiche.
    """
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='componenti')
    nome_componente = models.ForeignKey(TipoComponente, on_delete=models.PROTECT, help_text="Tipo di componente (es. Suola, Tacco)")
    colore = models.ForeignKey(Colore, on_delete=models.SET_NULL, null=True, blank=True, help_text="Colore specifico per questo componente in questo modello")
    # Rimosso: coppie_misure = models.ManyToManyField(CoppiaMisura, blank=True)
    # Le misure sono ora gestite tramite MisuraComponente
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Componenti del Modello"
        ordering = ['nome_componente__nome']
        # Potresti volere un unique_together per modello e nome_componente per evitare duplicati
        # unique_together = ['modello', 'nome_componente']


    def __str__(self):
        colore_str = f" ({self.colore})" if self.colore else ""
        return f"{self.nome_componente} per {self.modello.nome}{colore_str}"

    def get_absolute_url(self):
        # Assumendo che tu voglia andare al dettaglio del modello
        return reverse('modello_detail', kwargs={'pk': self.modello.pk})


class MisuraComponente(models.Model):
    """
    Modello intermedio per associare una CoppiaMisura specifica a un Componente.
    Questo permette di definire, ad esempio, che la Suola del ModelloX per il numero 45
    ha una lunghezza di 32cm.
    """
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name='misure_associate')
    coppia_misura = models.ForeignKey(CoppiaMisura, on_delete=models.PROTECT, help_text="La misura specifica (es. Lunghezza 32cm per taglia 45)")
    # Potresti aggiungere altri campi qui se necessario, ad esempio:
    # quantita_necessaria = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Quantità di questo componente per questa misura")

    class Meta:
        verbose_name_plural = "Misure dei Componenti"
        unique_together = ['componente', 'coppia_misura'] # Evita duplicati

    def __str__(self):
        return f"{self.componente} - {self.coppia_misura}"


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
        """
        Calcola i materiali necessari per questo ordine.
        Ora deve considerare le misure specifiche per ogni componente.
        """
        materiali = {} # Chiave: (TipoComponente.nome, Colore.nome o None), Valore: quantità
        
        for dettaglio_ordine in self.dettagli.all():
            # dettaglio_ordine.coppia_misura ora si riferisce a una "taglia di scarpa" generale per l'ordine
            # es. "Taglia 42"
            taglia_scarpa_ordinata = dettaglio_ordine.coppia_misura_scarpa # Rinominato per chiarezza
            quantita_per_taglia = dettaglio_ordine.quantita
            
            # Itera su tutti i componenti definiti per il modello di scarpa dell'ordine
            for componente_del_modello in self.modello.componenti.all():
                # Trova la MisuraComponente specifica per questo componente_del_modello
                # e per la taglia_scarpa_ordinata.
                # Questo presuppone che esista una MisuraComponente che collega
                # il componente_del_modello (es. "Suola") alla taglia_scarpa_ordinata (es. "Taglia 42")
                # tramite il campo 'numero_scarpa_riferimento' in CoppiaMisura.
                try:
                    misura_componente_specifica = MisuraComponente.objects.get(
                        componente=componente_del_modello,
                        coppia_misura__numero_scarpa_riferimento=taglia_scarpa_ordinata.numero_scarpa # Assumendo che CoppiaMisura abbia 'numero_scarpa'
                    )
                    # Se trovata, allora questo componente (con il suo colore) è necessario
                    key = (componente_del_modello.nome_componente.nome, componente_del_modello.colore)
                    materiali[key] = materiali.get(key, 0) + quantita_per_taglia
                except MisuraComponente.DoesNotExist:
                    # Gestisci il caso in cui non ci sia una misura specifica per quella taglia.
                    # Potrebbe essere un errore di configurazione o una logica diversa.
                    # Per ora, assumiamo che se non c'è, non viene contato.
                    # Oppure, potresti avere una misura "default" o "tutte le taglie".
                    # print(f"Attenzione: Misura non trovata per {componente_del_modello} e taglia {taglia_scarpa_ordinata.numero_scarpa}")
                    pass
                except MisuraComponente.MultipleObjectsReturned:
                    # print(f"Errore: Trovate misure multiple per {componente_del_modello} e taglia {taglia_scarpa_ordinata.numero_scarpa}")
                    pass


        return materiali


class DettaglioOrdine(models.Model):
    """
    Rappresenta una riga di un ordine, specificando la quantità per una data "taglia generica di scarpa".
    La `coppia_misura_scarpa` qui si riferisce alla taglia della scarpa finita (es. Taglia 42).
    Le misure specifiche dei singoli componenti (es. lunghezza suola per taglia 42) sono definite in MisuraComponente.
    """
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='dettagli')
    coppia_misura_scarpa = models.ForeignKey(CoppiaMisura, on_delete=models.CASCADE, help_text="Taglia della scarpa per questa riga d'ordine (es. Taglia 42)")
    quantita = models.IntegerField(validators=[MinValueValidator(1)])
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Dettagli Ordine (per Taglia Scarpa)"
        ordering = ['coppia_misura_scarpa__numero_scarpa_riferimento'] # o altro campo di CoppiaMisura per ordinare
        unique_together = ['ordine', 'coppia_misura_scarpa']

    def __str__(self):
        return f"{self.quantita}x {self.coppia_misura_scarpa} per Ordine #{self.ordine.id}"

    def get_absolute_url(self):
        # Potrebbe non essere necessario un URL diretto, ma se lo fosse:
        return reverse('ordine_detail', kwargs={'pk': self.ordine.pk})