from django.db import models
from django.utils import timezone
from apps.entreprise.models import Entreprise
from apps.employe.models import Employe

UNITE_CHOICES = [
    ('kg', 'Kilogramme'),
    ('g', 'Gramme'),
    ('unite', 'Unité'),
    ('L', 'Litre'),
    ('ml', 'Millilitre'),
    ('m', 'Mètre'),
    ('boite', 'Boîte'),
    ('kp', 'kapoaka'),
    ('md', 'madikao'),
    ('sac','Sac'),
    ('bt-1','bouteil 1 litre'),
    ('bt-1.5','bouteil 1,5 litre'),
    ('bt-2','bouteil 2 litre'),
]


class Stock(models.Model):
    nom = models.CharField(max_length=200)  
    description = models.TextField(default='')
    quantite = models.DecimalField(max_digits=12, decimal_places=2, default=0) 
    stock_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)  
    unite = models.CharField(max_length=10, choices=UNITE_CHOICES, default='kg')
    fournisseur = models.CharField(max_length=200)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='stocks')
    cree_par = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True, related_name='stocks_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nom} ({self.quantite} {self.unite})"
    
    @property
    def est_en_rupture(self):
        return self.quantite <= self.stock_min
    
    class Meta:
        db_table = 'stock'
        unique_together = ['nom', 'entreprise']

