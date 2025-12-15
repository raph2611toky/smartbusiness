from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from faker import Faker
import random
from datetime import datetime
from apps.users.models import User

class Command(BaseCommand):
    help = 'Seed the database with test users (2 spécifiques + 10 vendeurs + 40 clients)'

    def handle(self, *args, **kwargs):
        fake = Faker('fr_FR') 
        
        phone_prefixes = ['+26132', '+26133', '+26134']

        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Starting to seed users...'))

        # --- Utilisateurs spécifiques ---
        special_users = [
            {
                "nom_complet": "Nandrasana Toky",
                "email": "tokynandrasana2611@gmail.com",
                "sexe": "M",
                "password": "Raph26/11",
                "date_naissance": datetime.strptime("2003-11-26", "%Y-%m-%d"),
                "is_staff": True
            },
            {
                "nom_complet": "Razanaparany Jennysca",
                "email": "jennyscaladydi@gmail.com",
                "sexe": "F",
                "password": "Love2022.",
                "date_naissance": datetime.strptime("2003-06-08", "%Y-%m-%d"),
                "is_staff": False,
                "numero_phone":"+261321644765"
            }
        ]

        for u in special_users:
            user = User.objects.create(
                nom_complet=u["nom_complet"],
                email=u["email"],
                sexe=u["sexe"],
                password=make_password(u["password"]),
                date_naissance=u["date_naissance"],
                profile='users/profiles/default.png',
                numero_phone=u.get("numero_phone",f"{random.choice(phone_prefixes)}{fake.numerify('#######')}"),
                is_staff=u["is_staff"],
                is_verified=True,
                is_active=True,
                is_superuser=False,
                date_joined=datetime.now()
            )
            self.stdout.write(self.style.SUCCESS(f'Added special user: {u["nom_complet"]}'))
        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded users, vendors, and clients.'))
