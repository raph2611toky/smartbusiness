# apps/entreprise/management/commands/seed_employe.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.entreprise.models import (
    Acces, Profession, Employe, EmployeCompte, PrefixTelephone, 
    Devise, Entreprise
)
from faker import Faker
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seed employés, accès, professions'

    def handle(self, *args, **kwargs):
        fake = Faker('fr_FR')
        self.stdout.write(self.style.SUCCESS('Starting employe seed...'))

        # Nettoyage
        Employe.objects.all().delete()
        EmployeCompte.objects.all().delete()
        Acces.objects.all().delete()
        Profession.objects.all().delete()

        # 1. ACCES (Permissions)
        acces_data = [
            'Dashboard', 'Employés', 'Clients', 'Factures', 'Stocks', 
            'Commandes', 'Rapports', 'Paramètres', 'Comptabilité', 
            'Configuration', 'Export', 'Import', 'Notifications'
        ]
        
        acces_list = []
        for titre in acces_data:
            acces = Acces.objects.create(
                titre=titre,
                description=f"Accès au module {titre.lower()}",
                permissions={'read': True, 'write': True, 'delete': False}
            )
            acces_list.append(acces)

        # 2. PROFESSIONS avec accès associés
        professions_data = [
            {
                'nom': 'Directeur Général',
                'acces': ['Dashboard', 'Employés', 'Rapports', 'Paramètres', 'Configuration']
            },
            {
                'nom': 'Responsable Finance',
                'acces': ['Comptabilité', 'Factures', 'Rapports', 'Dashboard']
            },
            {
                'nom': 'Gestionnaire Stocks',
                'acces': ['Stocks', 'Commandes', 'Dashboard']
            },
            {
                'nom': 'Comptable',
                'acces': ['Comptabilité', 'Factures']
            },
            {
                'nom': 'Commercial',
                'acces': ['Clients', 'Factures', 'Commandes']
            },
            {
                'nom': 'Assistant Administratif',
                'acces': ['Employés', 'Dashboard']
            },
            {
                'nom': 'Magasinier',
                'acces': ['Stocks']
            }
        ]

        professions = []
        for prof_data in professions_data:
            profession = Profession.objects.create(
                nom=prof_data['nom'],
                description=f"Profession {prof_data['nom']}",
                couleur='#3B82F6' if 'Directeur' in prof_data['nom'] else '#10B981'
            )
            # Associer accès
            for acces_titre in prof_data['acces']:
                acces = Acces.objects.get(titre=acces_titre)
                profession.acces.add(acces)
            professions.append(profession)

        # 3. Obtenir entreprises et préfixes pour seed
        entreprises = Entreprise.objects.filter(est_actif=True)[:5]
        mg_prefix = PrefixTelephone.objects.filter(prefix='+261').first()

        if not entreprises.exists():
            self.stdout.write(self.style.WARNING('Aucune entreprise active pour seed employés'))
            return

        # 4. Créer employés (5 par entreprise)
        for entreprise in entreprises:
            for i in range(random.randint(3, 8)):
                employe = Employe.objects.create(
                    entreprise=entreprise,
                    nom_complet=fake.name(),
                    email=fake.email(),
                    date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=65),
                    cin=f"300{random.randint(100000, 999999)}",
                    prefix_telephone=mg_prefix,
                    numero_telephone=f"34{random.randint(10000000, 99999999)}",
                    adresse=fake.address(),
                    etat_civil=random.choice(['celibataire', 'marie', 'divorce']),
                    fonction=fake.job(),
                    profession=random.choice(professions),
                    date_embauche=fake.date_this_decade()
                )
                
                # 30% ont un compte
                if random.random() < 0.3:
                    EmployeCompte.objects.create(
                        employe=employe,
                        mot_de_passe=make_password('password123'),
                        est_actif=random.choice([True, False])
                    )

        self.stdout.write(self.style.SUCCESS('✅ Seed employé terminé!'))
        self.stdout.write(self.style.SUCCESS(f'📊 {Acces.objects.count()} accès créés'))
        self.stdout.write(self.style.SUCCESS(f'🎭 {Profession.objects.count()} professions créées'))
        self.stdout.write(self.style.SUCCESS(f'👥 {Employe.objects.count()} employés créés'))
