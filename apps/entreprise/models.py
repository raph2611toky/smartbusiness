# Updated apps/entreprise/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone as django_timezone
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

def default_created_at():
    tz = os.getenv("TIMEZONE_HOURS")
    if tz.strip().startswith("-"):
        return django_timezone.now() - timedelta(hours=int(tz.replace("-","").strip()))
    return django_timezone.now() + timedelta(hours=int(tz))

class Devise(models.Model):
    nom_court = models.CharField(max_length=3)
    nom_long = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    pays = models.TextField()
    drapeau_image = models.ImageField(upload_to='devises/drapeaux/', null=True, blank=True)

    def __str__(self):
        return self.nom_court

    class Meta:
        db_table = "devise"

class PrefixTelephone(models.Model):
    prefix = models.CharField(max_length=5)
    description = models.TextField(null=True, blank=True)
    pays = models.TextField()
    drapeau_image = models.ImageField(upload_to='prefixes/drapeaux/', null=True, blank=True)

    def __str__(self):
        return self.prefix

    class Meta:
        db_table = "prefix_telephone"

class Plan(models.Model):
    nom = models.CharField(max_length=50, unique=True)  # par exemple, 'freemium', 'pro', 'max'
    description = models.TextField(null=True, blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Optionnel, freemium pourrait être 0
    devise = models.ForeignKey(Devise, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nom

    class Meta:
        db_table = "plan"

class Service(models.Model):
    titre = models.CharField(max_length=100)

    def __str__(self):
        return self.titre

    class Meta:
        db_table = "service"

class Entreprise(models.Model):
    TYPE_CHOICES = [
        ('SARL', 'Société à Responsabilité Limitée'),
        ('SA', 'Société Anonyme'),
        ('SAS', 'Société par Actions Simplifiée'),
        ('EURL', 'Entreprise Unipersonnelle à Responsabilité Limitée'),
        ('EI', 'Entreprise Individuelle'),
        ('AUTRE', 'Autre'),
    ]

    nom_complet = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=250)
    nif_stat = models.CharField(max_length=100, null=True, blank=True)
    date_creation = models.DateTimeField(null=True, blank=True)
    profile = models.ImageField(upload_to='entreprise/profiles', default='entreprise/profiles/default.png')
    prefix_telephone = models.ForeignKey(PrefixTelephone, on_delete=models.SET_NULL, null=True, blank=True)
    numero_telephone = models.CharField(max_length=100)
    est_verifie = models.BooleanField(default=False)
    est_actif = models.BooleanField(default=False)
    services = models.ManyToManyField(Service, related_name="entreprises")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name="entreprises")
    type_entreprise = models.CharField(max_length=50, choices=TYPE_CHOICES, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom_complet', 'date_creation']

    def __str__(self):
        return self.nom_complet

    class Meta:
        db_table = 'entreprise'

class EntrepriseOtp(models.Model):
    code_otp = models.CharField(max_length=100)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name="otps")
    date_expiration = models.DateTimeField()
    date_creation = models.DateTimeField(default=default_created_at)

    def __str__(self):
        return self.code_otp

    class Meta:
        db_table = "entrepriseotp"

class EntrepriseOutstandingToken(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='outstanding_tokens')
    jti = models.CharField(max_length=255, unique=True)
    token = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    est_blackliste = models.BooleanField(default=False)

    def est_expire(self):
        return self.date_expiration <= django_timezone.now()

    class Meta:
        db_table = 'entrepriseoutstandingtoken'