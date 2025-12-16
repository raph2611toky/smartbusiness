from django.db import models
from django.utils import timezone
from apps.entreprise.models import Entreprise, PrefixTelephone
from apps.employe.models import Employe

STATUT_CHOICES = [
    ('brouillon', 'Brouillon'),
    ('envoyee', 'Envoyée'),
    ('payee', 'Payée'),
    ('annulee', 'Annulée'),
    ('echoue', 'Échoue'),
]

class Facture(models.Model):
    numero = models.CharField(max_length=50, unique=True)  # FAC-2025-001
    client = models.CharField(max_length=200)
    montant = models.DecimalField(max_digits=12, decimal_places=2)  # 15000.00
    prefix_telephone = models.ForeignKey(PrefixTelephone, on_delete=models.SET_DEFAULT, default=125)
    date_facture = models.DateField()
    date_echeance = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    motif = models.TextField(blank=True, null=True)  # Description détaillée
    description = models.TextField(blank=True, null=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='factures')
    cree_par = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.numero} - {self.client.nom}"
    
    @property
    def est_payee(self):
        return self.statut == 'payee'
    
    @property
    def est_echue(self):
        return self.statut == 'echue' or (self.statut == 'envoyee' and timezone.now().date() > self.date_echeance)
    
    class Meta:
        db_table = 'finance_facture'
        ordering = ['-date_creation']
