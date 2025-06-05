from django.db import models
from django.urls import reverse # Assicurati che non ci sia 'gestionale:' se non usi namespace
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
    descrizione_misura = models.CharField(max_length=100, help_text="Es. 'Taglia 42', 'Lunghezza 10cm per tacco'") # Rimosso default problematico
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
        new_modello = Modello.objects.create(
            cliente=self.cliente,
            nome=new_name or f"{self.nome} (Copia {timezone.now().strftime('%Y%m%d%H%M%S')})",
            tipo=self.tipo,
            note=self.note,
            created_by=self.created_by
        )
        for componente_originale in self.componenti.all():
            new_componente = Componente.objects.create(
                modello=new_modello,
                nome_componente=componente_originale.nome_componente,
                colore=componente_originale.colore,
                note=componente_originale.note
            )
            for misura_comp_originale in componente_originale.misure_associate.all():
                # Assumendo che MisuraComponente NON abbia 'quantita_necessaria' come da tua ultima definizione
                MisuraComponente.objects.create(
                    componente=new_componente,
                    coppia_misura=misura_comp_originale.coppia_misura
                )
        return new_modello

class TipoComponente(models.Model):
    nome = models.CharField(max_length=100, unique=True) # Rimosso default problematico
    descrizione = models.TextField(blank=True, null=True) # Rimosso default, opzionale

    class Meta:
        verbose_name_plural = "Tipi Componente"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Componente(models.Model):
    modello = models.ForeignKey(Modello, on_delete=models.CASCADE, related_name='componenti')
    nome_componente = models.ForeignKey(TipoComponente, on_delete=models.PROTECT, help_text="Tipo di componente (es. Suola, Tacco)") # Rimosso default problematico
    colore = models.ForeignKey(Colore, on_delete=models.SET_NULL, null=True, blank=True, help_text="Colore specifico per questo componente in questo modello") # Rimosso default problematico
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Componenti del Modello"
        ordering = ['nome_componente__nome']

    def __str__(self):
        colore_str = f" ({self.colore})" if self.colore else ""
        # Gestisce il caso in cui nome_componente potrebbe essere None se fosse nullable (ma non lo è più)
        nome_comp_str = self.nome_componente.nome if self.nome_componente else "N/D"
        return f"{nome_comp_str} per {self.modello.nome}{colore_str}"

    def get_absolute_url(self):
        return reverse('modello_detail', kwargs={'pk': self.modello.pk})


class MisuraComponente(models.Model):
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name='misure_associate')
    coppia_misura = models.ForeignKey(CoppiaMisura, on_delete=models.PROTECT, help_text="La misura specifica (es. Lunghezza 32cm per taglia 45)")

    class Meta:
        verbose_name_plural = "Misure dei Componenti"
        unique_together = ['componente', 'coppia_misura']

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
        return f"Ordine #{self.id} - {self.modello.nome} ({self.get_stato_display()})" # Usato modello.nome per evitare ricorsione se __str__ di modello include cliente

    def get_absolute_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.pk})

    @property
    def quantita_totale(self):
        return sum(dettaglio.quantita for dettaglio in self.dettagli.all())

    def get_materiali_necessari(self):
        materiali = {}
        for dettaglio_ordine in self.dettagli.all():
            taglia_scarpa_ordinata = dettaglio_ordine.coppia_misura_scarpa # NOME CORRETTO QUI
            quantita_per_taglia = dettaglio_ordine.quantita

            for componente_del_modello in self.modello.componenti.all():
                try:
                    # Assumendo che CoppiaMisura usato per taglia_scarpa_ordinata abbia il campo 'numero_scarpa_riferimento'
                    # e che MisuraComponente usi CoppiaMisura che si riferisce a questa taglia.
                    misura_componente_specifica = MisuraComponente.objects.get(
                        componente=componente_del_modello,
                        coppia_misura__numero_scarpa_riferimento=taglia_scarpa_ordinata.numero_scarpa_riferimento # NOME CAMPO CORRETTO QUI
                    )
                    # Se trovata, allora questo componente (con il suo colore) è necessario
                    key = (componente_del_modello.nome_componente.nome, componente_del_modello.colore.nome if componente_del_modello.colore else None)
                    materiali[key] = materiali.get(key, 0) + quantita_per_taglia
                except MisuraComponente.DoesNotExist:
                    pass
                except MisuraComponente.MultipleObjectsReturned:
                    # Logga questo errore, è importante
                    print(f"ERRORE: Trovate misure multiple per {componente_del_modello} e taglia rif. {taglia_scarpa_ordinata.numero_scarpa_riferimento}")
                    pass
        return materiali


class DettaglioOrdine(models.Model):
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='dettagli')
    # Nome campo CORRETTO qui e nel Meta
    coppia_misura_scarpa = models.ForeignKey(CoppiaMisura, on_delete=models.CASCADE, help_text="Taglia della scarpa per questa riga d'ordine (es. Taglia 42)")
    quantita = models.IntegerField(validators=[MinValueValidator(1)])
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Dettagli Ordine (per Taglia Scarpa)"
        ordering = ['coppia_misura_scarpa__numero_scarpa_riferimento'] # Nome CORRETTO
        unique_together = ['ordine', 'coppia_misura_scarpa'] # Nome CORRETTO

    def __str__(self):
        # Assicurati che coppia_misura_scarpa sia definito. Potrebbe essere None se nullable (ma non lo è)
        nome_misura = str(self.coppia_misura_scarpa) if self.coppia_misura_scarpa else "N/D"
        return f"{self.quantita}x {nome_misura} per Ordine #{self.ordine.id}"

    def get_absolute_url(self):
        return reverse('ordine_detail', kwargs={'pk': self.ordine.pk})