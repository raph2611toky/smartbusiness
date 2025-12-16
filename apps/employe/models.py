# apps/entreprise/models/employe.py
from django.db import models
from django.utils import timezone as django_timezone
from django.contrib.auth.hashers import make_password
from apps.entreprise.models import Entreprise, PrefixTelephone, default_created_at, Devise

class Acces(models.Model):
    titre = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    permissions = models.JSONField(default=dict, blank=True, null=True)  # Permissions granulaires
    
    def __str__(self):
        return self.titre
    
    class Meta:
        db_table = "acces"

class Profession(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    acces = models.ManyToManyField(Acces, related_name="professions")
    couleur = models.CharField(max_length=7, default="#3B82F6")  # Hex color pour UI
    
    def __str__(self):
        return self.nom
    
    class Meta:
        db_table = "profession"

class Employe(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name="employes")
    nom_complet = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    date_naissance = models.DateField(null=True, blank=True)
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    renumeration = models.BigIntegerField(default=0)
    renumeration_devise = models.ForeignKey(Devise, on_delete=models.SET_DEFAULT, default=125)
    prefix_telephone = models.ForeignKey(
        PrefixTelephone, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="employes"
    )
    numero_telephone = models.CharField(max_length=15, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    etat_civil = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        choices=[
            ('celibataire', 'Célibataire'),
            ('marie', 'Marié(e)'),
            ('divorce', 'Divorcé(e)'),
            ('veuf', 'Veuf(ve)')
        ]
    )
    fonction = models.CharField(max_length=200)
    photo = models.ImageField(
        upload_to='employes/profiles/', 
        null=True, 
        blank=True,
        default='employes/profiles/default.png'
    )
    est_verifie = models.BooleanField(default=False)
    est_actif = models.BooleanField(default=True)
    date_embauche = models.DateField(null=True, blank=True)
    date_sortie = models.DateField(null=True, blank=True)
    est_un_compte = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=default_created_at)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom_complet} ({self.entreprise.nom_complet})"
    
    class Meta:
        db_table = "employe"
        unique_together = ['entreprise', 'cin']

class EmployeCompte(models.Model):
    employe = models.OneToOneField(
        Employe, 
        on_delete=models.CASCADE, 
        related_name="compte"
    )
    mot_de_passe = models.CharField(max_length=255) 
    est_actif = models.BooleanField(default=False)
    dernier_login = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(default=default_created_at)
    nombre_tentatives = models.PositiveIntegerField(default=0)
    profession = models.ForeignKey(
        Profession, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="employes"
    )
    bloque_jusqua = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.mot_de_passe = make_password(raw_password)
    
    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.mot_de_passe)
    
    def __str__(self):
        return self.employe.nom_complet
    
    class Meta:
        db_table = "employecompte"

class EmployeOtp(models.Model):
    code_otp = models.CharField(max_length=6)
    employe = models.ForeignKey(
        Employe, 
        on_delete=models.CASCADE, 
        related_name="otps"
    )
    date_expiration = models.DateTimeField()
    date_creation = models.DateTimeField(default=default_created_at)
    utilise = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.code_otp} - {self.employe.nom_complet}"
    
    class Meta:
        db_table = "employeotp"

class EmployeOutstandingToken(models.Model):
    employe = models.ForeignKey(
        Employe, 
        on_delete=models.CASCADE, 
        related_name='outstanding_tokens'
    )
    jti = models.CharField(max_length=255, unique=True)
    token = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    est_blackliste = models.BooleanField(default=False)

    def est_expire(self):
        return self.date_expiration <= django_timezone.now()
    
    class Meta:
        db_table = 'employeoutstandingtoken'
