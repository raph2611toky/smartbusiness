# apps/entreprise/management/commands/seed_entreprise.py
from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import datetime
from apps.entreprise.models import Devise, PrefixTelephone, Plan, Service

class Command(BaseCommand):
    help = 'Seed the database with test data for entreprise app (devises, prefixes, plans, services)'

    def handle(self, *args, **kwargs):
        fake = Faker('fr_FR')
        self.stdout.write(self.style.SUCCESS('Starting to seed entreprise...'))

        # Delete existing data
        Devise.objects.all().delete()
        PrefixTelephone.objects.all().delete()
        Plan.objects.all().delete()
        Service.objects.all().delete()

        pays_data = [
            {"code": "AFN", "name": "Afghan afghani", "prefix": "+93", "countries": "Afghanistan"},
            {"code": "EUR", "name": "Euro", "prefix": "+376", "countries": "Andorra"},
            {"code": "EUR", "name": "Euro", "prefix": "+33", "countries": "France"},  # Représente souvent l'Eurozone
            {"code": "EUR", "name": "Euro", "prefix": "+376", "countries": "Andorre / Eurozone (ex. France +33, Allemagne +49, etc.)"},  # Note pour les multiples
            {"code": "ALL", "name": "Albanian lek", "prefix": "+355", "countries": "Albania"},
            {"code": "DZD", "name": "Algerian dinar", "prefix": "+213", "countries": "Algeria"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-684", "countries": "American Samoa"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-264", "countries": "Anguilla"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-268", "countries": "Antigua and Barbuda"},
            {"code": "ARS", "name": "Argentine peso", "prefix": "+54", "countries": "Argentina"},
            {"code": "AMD", "name": "Armenian dram", "prefix": "+374", "countries": "Armenia"},
            {"code": "AUD", "name": "Australian dollar", "prefix": "+61", "countries": "Australia"},
            {"code": "EUR", "name": "Euro", "prefix": "+43", "countries": "Austria"},
            {"code": "AZN", "name": "Azerbaijani manat", "prefix": "+994", "countries": "Azerbaijan"},
            {"code": "BSD", "name": "Bahamian dollar", "prefix": "+1-242", "countries": "Bahamas"},
            {"code": "BHD", "name": "Bahraini dinar", "prefix": "+973", "countries": "Bahrain"},
            {"code": "BDT", "name": "Bangladeshi taka", "prefix": "+880", "countries": "Bangladesh"},
            {"code": "BBD", "name": "Barbadian dollar", "prefix": "+1-246", "countries": "Barbados"},
            {"code": "BYN", "name": "Belarusian ruble", "prefix": "+375", "countries": "Belarus"},
            {"code": "EUR", "name": "Euro", "prefix": "+32", "countries": "Belgium"},
            {"code": "BZD", "name": "Belize dollar", "prefix": "+501", "countries": "Belize"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+229", "countries": "Benin"},
            {"code": "BMD", "name": "Bermudian dollar", "prefix": "+1-441", "countries": "Bermuda"},
            {"code": "BTN", "name": "Bhutanese ngultrum", "prefix": "+975", "countries": "Bhutan"},
            {"code": "BOB", "name": "Bolivian boliviano", "prefix": "+591", "countries": "Bolivia"},
            {"code": "USD", "name": "United States dollar", "prefix": "+599", "countries": "Bonaire, Sint Eustatius and Saba"},
            {"code": "BAM", "name": "Bosnia and Herzegovina convertible mark", "prefix": "+387", "countries": "Bosnia and Herzegovina"},
            {"code": "BWP", "name": "Botswana pula", "prefix": "+267", "countries": "Botswana"},
            {"code": "BRL", "name": "Brazilian real", "prefix": "+55", "countries": "Brazil"},
            {"code": "GBP", "name": "Pound sterling", "prefix": "+1-284", "countries": "British Virgin Islands"},
            {"code": "BND", "name": "Brunei dollar", "prefix": "+673", "countries": "Brunei"},
            {"code": "BGN", "name": "Bulgarian lev", "prefix": "+359", "countries": "Bulgaria"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+226", "countries": "Burkina Faso"},
            {"code": "BIF", "name": "Burundian franc", "prefix": "+257", "countries": "Burundi"},
            {"code": "KHR", "name": "Cambodian riel", "prefix": "+855", "countries": "Cambodia"},
            {"code": "XAF", "name": "CFA franc BEAC", "prefix": "+237", "countries": "Cameroon"},
            {"code": "CAD", "name": "Canadian dollar", "prefix": "+1", "countries": "Canada"},
            {"code": "CVE", "name": "Cape Verdean escudo", "prefix": "+238", "countries": "Cape Verde"},
            {"code": "KYD", "name": "Cayman Islands dollar", "prefix": "+1-345", "countries": "Cayman Islands"},
            {"code": "XAF", "name": "CFA franc BEAC", "prefix": "+236", "countries": "Central African Republic"},
            {"code": "XAF", "name": "CFA franc BEAC", "prefix": "+235", "countries": "Chad"},
            {"code": "CLP", "name": "Chilean peso", "prefix": "+56", "countries": "Chile"},
            {"code": "CNY", "name": "Renminbi", "prefix": "+86", "countries": "China"},
            {"code": "COP", "name": "Colombian peso", "prefix": "+57", "countries": "Colombia"},
            {"code": "KMF", "name": "Comorian franc", "prefix": "+269", "countries": "Comoros"},
            {"code": "CDF", "name": "Congolese franc", "prefix": "+243", "countries": "Democratic Republic of the Congo"},
            {"code": "XAF", "name": "CFA franc BEAC", "prefix": "+242", "countries": "Republic of the Congo"},
            {"code": "CRC", "name": "Costa Rican colón", "prefix": "+506", "countries": "Costa Rica"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+225", "countries": "Ivory Coast"},
            {"code": "HRK", "name": "Croatian kuna", "prefix": "+385", "countries": "Croatia"},  # Note: remplacé par EUR en 2023, mais historique
            {"code": "CUP", "name": "Cuban peso", "prefix": "+53", "countries": "Cuba"},
            {"code": "ANG", "name": "Netherlands Antillean guilder", "prefix": "+599", "countries": "Curaçao"},
            {"code": "EUR", "name": "Euro", "prefix": "+357", "countries": "Cyprus"},
            {"code": "CZK", "name": "Czech koruna", "prefix": "+420", "countries": "Czech Republic"},
            {"code": "DKK", "name": "Danish krone", "prefix": "+45", "countries": "Denmark"},
            {"code": "DJF", "name": "Djiboutian franc", "prefix": "+253", "countries": "Djibouti"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-767", "countries": "Dominica"},
            {"code": "DOP", "name": "Dominican peso", "prefix": "+1-809", "countries": "Dominican Republic"},
            {"code": "USD", "name": "United States dollar", "prefix": "+593", "countries": "Ecuador"},
            {"code": "EGP", "name": "Egyptian pound", "prefix": "+20", "countries": "Egypt"},
            {"code": "USD", "name": "United States dollar", "prefix": "+503", "countries": "El Salvador"},
            {"code": "XAF", "name": "CFA franc BEAC", "prefix": "+240", "countries": "Equatorial Guinea"},
            {"code": "ERN", "name": "Eritrean nakfa", "prefix": "+291", "countries": "Eritrea"},
            {"code": "EUR", "name": "Euro", "prefix": "+372", "countries": "Estonia"},
            {"code": "SZL", "name": "Swazi lilangeni", "prefix": "+268", "countries": "Eswatini"},
            {"code": "ETB", "name": "Ethiopian birr", "prefix": "+251", "countries": "Ethiopia"},
            {"code": "EUR", "name": "Euro", "prefix": "+358", "countries": "Finland"},
            {"code": "XPF", "name": "CFP franc", "prefix": "+689", "countries": "French Polynesia"},
            {"code": "XAF", "name": "CFA franc BEAC", "prefix": "+241", "countries": "Gabon"},
            {"code": "GMD", "name": "Gambian dalasi", "prefix": "+220", "countries": "Gambia"},
            {"code": "GEL", "name": "Georgian lari", "prefix": "+995", "countries": "Georgia"},
            {"code": "EUR", "name": "Euro", "prefix": "+49", "countries": "Germany"},
            {"code": "GHS", "name": "Ghanaian cedi", "prefix": "+233", "countries": "Ghana"},
            {"code": "GBP", "name": "Pound sterling", "prefix": "+350", "countries": "Gibraltar"},
            {"code": "EUR", "name": "Euro", "prefix": "+30", "countries": "Greece"},
            {"code": "DKK", "name": "Danish krone", "prefix": "+299", "countries": "Greenland"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-473", "countries": "Grenada"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-671", "countries": "Guam"},
            {"code": "GTQ", "name": "Guatemalan quetzal", "prefix": "+502", "countries": "Guatemala"},
            {"code": "GBP", "name": "Pound sterling", "prefix": "+44", "countries": "Guernsey"},
            {"code": "GNF", "name": "Guinean franc", "prefix": "+224", "countries": "Guinea"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+245", "countries": "Guinea-Bissau"},
            {"code": "GYD", "name": "Guyanese dollar", "prefix": "+592", "countries": "Guyana"},
            {"code": "HTG", "name": "Haitian gourde", "prefix": "+509", "countries": "Haiti"},
            {"code": "HNL", "name": "Honduran lempira", "prefix": "+504", "countries": "Honduras"},
            {"code": "HKD", "name": "Hong Kong dollar", "prefix": "+852", "countries": "Hong Kong"},
            {"code": "HUF", "name": "Hungarian forint", "prefix": "+36", "countries": "Hungary"},
            {"code": "ISK", "name": "Icelandic króna", "prefix": "+354", "countries": "Iceland"},
            {"code": "INR", "name": "Indian rupee", "prefix": "+91", "countries": "India"},
            {"code": "IDR", "name": "Indonesian rupiah", "prefix": "+62", "countries": "Indonesia"},
            {"code": "IRR", "name": "Iranian rial", "prefix": "+98", "countries": "Iran"},
            {"code": "IQD", "name": "Iraqi dinar", "prefix": "+964", "countries": "Iraq"},
            {"code": "EUR", "name": "Euro", "prefix": "+353", "countries": "Ireland"},
            {"code": "GBP", "name": "Pound sterling", "prefix": "+44", "countries": "Isle of Man"},
            {"code": "ILS", "name": "Israeli new shekel", "prefix": "+972", "countries": "Israel"},
            {"code": "EUR", "name": "Euro", "prefix": "+39", "countries": "Italy"},
            {"code": "JMD", "name": "Jamaican dollar", "prefix": "+1-876", "countries": "Jamaica"},
            {"code": "JPY", "name": "Japanese yen", "prefix": "+81", "countries": "Japan"},
            {"code": "GBP", "name": "Pound sterling", "prefix": "+44", "countries": "Jersey"},
            {"code": "JOD", "name": "Jordanian dinar", "prefix": "+962", "countries": "Jordan"},
            {"code": "KZT", "name": "Kazakhstani tenge", "prefix": "+7", "countries": "Kazakhstan"},
            {"code": "KES", "name": "Kenyan shilling", "prefix": "+254", "countries": "Kenya"},
            {"code": "AUD", "name": "Australian dollar", "prefix": "+686", "countries": "Kiribati"},
            {"code": "KPW", "name": "North Korean won", "prefix": "+850", "countries": "North Korea"},
            {"code": "KRW", "name": "South Korean won", "prefix": "+82", "countries": "South Korea"},
            {"code": "KWD", "name": "Kuwaiti dinar", "prefix": "+965", "countries": "Kuwait"},
            {"code": "KGS", "name": "Kyrgyzstani som", "prefix": "+996", "countries": "Kyrgyzstan"},
            {"code": "LAK", "name": "Lao kip", "prefix": "+856", "countries": "Laos"},
            {"code": "EUR", "name": "Euro", "prefix": "+371", "countries": "Latvia"},
            {"code": "LBP", "name": "Lebanese pound", "prefix": "+961", "countries": "Lebanon"},
            {"code": "LSL", "name": "Lesotho loti", "prefix": "+266", "countries": "Lesotho"},
            {"code": "LRD", "name": "Liberian dollar", "prefix": "+231", "countries": "Liberia"},
            {"code": "LYD", "name": "Libyan dinar", "prefix": "+218", "countries": "Libya"},
            {"code": "CHF", "name": "Swiss franc", "prefix": "+423", "countries": "Liechtenstein"},
            {"code": "EUR", "name": "Euro", "prefix": "+370", "countries": "Lithuania"},
            {"code": "EUR", "name": "Euro", "prefix": "+352", "countries": "Luxembourg"},
            {"code": "MOP", "name": "Macanese pataca", "prefix": "+853", "countries": "Macao"},
            {"code": "MKD", "name": "Macedonian denar", "prefix": "+389", "countries": "North Macedonia"},
            {"code": "MGA", "name": "Malagasy ariary", "prefix": "+261", "countries": "Madagascar"},
            {"code": "MWK", "name": "Malawian kwacha", "prefix": "+265", "countries": "Malawi"},
            {"code": "MYR", "name": "Malaysian ringgit", "prefix": "+60", "countries": "Malaysia"},
            {"code": "MVR", "name": "Maldivian rufiyaa", "prefix": "+960", "countries": "Maldives"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+223", "countries": "Mali"},
            {"code": "EUR", "name": "Euro", "prefix": "+356", "countries": "Malta"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-670", "countries": "Northern Mariana Islands"},
            {"code": "MAD", "name": "Moroccan dirham", "prefix": "+212", "countries": "Morocco"},
            {"code": "MUR", "name": "Mauritian rupee", "prefix": "+230", "countries": "Mauritius"},
            {"code": "MXN", "name": "Mexican peso", "prefix": "+52", "countries": "Mexico"},
            {"code": "USD", "name": "United States dollar", "prefix": "+691", "countries": "Micronesia"},
            {"code": "MDL", "name": "Moldovan leu", "prefix": "+373", "countries": "Moldova"},
            {"code": "EUR", "name": "Euro", "prefix": "+377", "countries": "Monaco"},
            {"code": "MNT", "name": "Mongolian tögrög", "prefix": "+976", "countries": "Mongolia"},
            {"code": "EUR", "name": "Euro", "prefix": "+382", "countries": "Montenegro"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-664", "countries": "Montserrat"},
            {"code": "ZAR", "name": "South African rand", "prefix": "+258", "countries": "Mozambique"},
            {"code": "MMK", "name": "Burmese kyat", "prefix": "+95", "countries": "Myanmar"},
            {"code": "NAD", "name": "Namibian dollar", "prefix": "+264", "countries": "Namibia"},
            {"code": "AUD", "name": "Australian dollar", "prefix": "+674", "countries": "Nauru"},
            {"code": "NPR", "name": "Nepalese rupee", "prefix": "+977", "countries": "Nepal"},
            {"code": "EUR", "name": "Euro", "prefix": "+31", "countries": "Netherlands"},
            {"code": "XPF", "name": "CFP franc", "prefix": "+687", "countries": "New Caledonia"},
            {"code": "NZD", "name": "New Zealand dollar", "prefix": "+64", "countries": "New Zealand"},
            {"code": "NIO", "name": "Nicaraguan córdoba", "prefix": "+505", "countries": "Nicaragua"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+227", "countries": "Niger"},
            {"code": "NGN", "name": "Nigerian naira", "prefix": "+234", "countries": "Nigeria"},
            {"code": "NOK", "name": "Norwegian krone", "prefix": "+47", "countries": "Norway"},
            {"code": "OMR", "name": "Omani rial", "prefix": "+968", "countries": "Oman"},
            {"code": "PKR", "name": "Pakistani rupee", "prefix": "+92", "countries": "Pakistan"},
            {"code": "USD", "name": "United States dollar", "prefix": "+680", "countries": "Palau"},
            {"code": "PAB", "name": "Panamanian balboa", "prefix": "+507", "countries": "Panama"},
            {"code": "PGK", "name": "Papua New Guinean kina", "prefix": "+675", "countries": "Papua New Guinea"},
            {"code": "PYG", "name": "Paraguayan guaraní", "prefix": "+595", "countries": "Paraguay"},
            {"code": "PEN", "name": "Peruvian sol", "prefix": "+51", "countries": "Peru"},
            {"code": "PHP", "name": "Philippine peso", "prefix": "+63", "countries": "Philippines"},
            {"code": "PLN", "name": "Polish złoty", "prefix": "+48", "countries": "Poland"},
            {"code": "EUR", "name": "Euro", "prefix": "+351", "countries": "Portugal"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-787", "countries": "Puerto Rico"},
            {"code": "QAR", "name": "Qatari riyal", "prefix": "+974", "countries": "Qatar"},
            {"code": "EUR", "name": "Euro", "prefix": "+40", "countries": "Romania"},
            {"code": "RUB", "name": "Russian ruble", "prefix": "+7", "countries": "Russia"},
            {"code": "RWF", "name": "Rwandan franc", "prefix": "+250", "countries": "Rwanda"},
            {"code": "EUR", "name": "Euro", "prefix": "+590", "countries": "Saint Barthélemy"},
            {"code": "SHP", "name": "Saint Helena pound", "prefix": "+290", "countries": "Saint Helena"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-869", "countries": "Saint Kitts and Nevis"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-758", "countries": "Saint Lucia"},
            {"code": "EUR", "name": "Euro", "prefix": "+590", "countries": "Saint Martin (French part)"},
            {"code": "EUR", "name": "Euro", "prefix": "+508", "countries": "Saint Pierre and Miquelon"},
            {"code": "XCD", "name": "East Caribbean dollar", "prefix": "+1-784", "countries": "Saint Vincent and the Grenadines"},
            {"code": "WST", "name": "Samoan tālā", "prefix": "+685", "countries": "Samoa"},
            {"code": "EUR", "name": "Euro", "prefix": "+378", "countries": "San Marino"},
            {"code": "SAR", "name": "Saudi riyal", "prefix": "+966", "countries": "Saudi Arabia"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+221", "countries": "Senegal"},
            {"code": "RSD", "name": "Serbian dinar", "prefix": "+381", "countries": "Serbia"},
            {"code": "SCR", "name": "Seychellois rupee", "prefix": "+248", "countries": "Seychelles"},
            {"code": "SLE", "name": "Sierra Leonean leone", "prefix": "+232", "countries": "Sierra Leone"},
            {"code": "SGD", "name": "Singapore dollar", "prefix": "+65", "countries": "Singapore"},
            {"code": "EUR", "name": "Euro", "prefix": "+421", "countries": "Slovakia"},
            {"code": "EUR", "name": "Euro", "prefix": "+386", "countries": "Slovenia"},
            {"code": "SBD", "name": "Solomon Islands dollar", "prefix": "+677", "countries": "Solomon Islands"},
            {"code": "SOS", "name": "Somali shilling", "prefix": "+252", "countries": "Somalia"},
            {"code": "ZAR", "name": "South African rand", "prefix": "+27", "countries": "South Africa"},
            {"code": "SSP", "name": "South Sudanese pound", "prefix": "+211", "countries": "South Sudan"},
            {"code": "EUR", "name": "Euro", "prefix": "+34", "countries": "Spain"},
            {"code": "LKR", "name": "Sri Lankan rupee", "prefix": "+94", "countries": "Sri Lanka"},
            {"code": "SDG", "name": "Sudanese pound", "prefix": "+249", "countries": "Sudan"},
            {"code": "SRD", "name": "Surinamese dollar", "prefix": "+597", "countries": "Suriname"},
            {"code": "SEK", "name": "Swedish krona", "prefix": "+46", "countries": "Sweden"},
            {"code": "CHF", "name": "Swiss franc", "prefix": "+41", "countries": "Switzerland"},
            {"code": "SYP", "name": "Syrian pound", "prefix": "+963", "countries": "Syria"},
            {"code": "TWD", "name": "New Taiwan dollar", "prefix": "+886", "countries": "Taiwan"},
            {"code": "TJS", "name": "Tajikistani somoni", "prefix": "+992", "countries": "Tajikistan"},
            {"code": "TZS", "name": "Tanzanian shilling", "prefix": "+255", "countries": "Tanzania"},
            {"code": "THB", "name": "Thai baht", "prefix": "+66", "countries": "Thailand"},
            {"code": "XOF", "name": "CFA franc BCEAO", "prefix": "+228", "countries": "Togo"},
            {"code": "NZD", "name": "New Zealand dollar", "prefix": "+690", "countries": "Tokelau"},
            {"code": "TOP", "name": "Tongan paʻanga", "prefix": "+676", "countries": "Tonga"},
            {"code": "TTD", "name": "Trinidad and Tobago dollar", "prefix": "+1-868", "countries": "Trinidad and Tobago"},
            {"code": "TND", "name": "Tunisian dinar", "prefix": "+216", "countries": "Tunisia"},
            {"code": "TRY", "name": "Turkish lira", "prefix": "+90", "countries": "Turkey"},
            {"code": "TMT", "name": "Turkmenistani manat", "prefix": "+993", "countries": "Turkmenistan"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-649", "countries": "Turks and Caicos Islands"},
            {"code": "AUD", "name": "Australian dollar", "prefix": "+688", "countries": "Tuvalu"},
            {"code": "UGX", "name": "Ugandan shilling", "prefix": "+256", "countries": "Uganda"},
            {"code": "UAH", "name": "Ukrainian hryvnia", "prefix": "+380", "countries": "Ukraine"},
            {"code": "AED", "name": "United Arab Emirates dirham", "prefix": "+971", "countries": "United Arab Emirates"},
            {"code": "GBP", "name": "Pound sterling", "prefix": "+44", "countries": "United Kingdom"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1", "countries": "United States"},
            {"code": "UYU", "name": "Uruguayan peso", "prefix": "+598", "countries": "Uruguay"},
            {"code": "UZS", "name": "Uzbekistani soʻm", "prefix": "+998", "countries": "Uzbekistan"},
            {"code": "VUV", "name": "Vanuatu vatu", "prefix": "+678", "countries": "Vanuatu"},
            {"code": "VEF", "name": "Venezuelan bolívar", "prefix": "+58", "countries": "Venezuela"},
            {"code": "VND", "name": "Vietnamese đồng", "prefix": "+84", "countries": "Vietnam"},
            {"code": "USD", "name": "United States dollar", "prefix": "+1-340", "countries": "U.S. Virgin Islands"},
            {"code": "XPF", "name": "CFP franc", "prefix": "+681", "countries": "Wallis and Futuna"},
            {"code": "YER", "name": "Yemeni rial", "prefix": "+967", "countries": "Yemen"},
            {"code": "ZMW", "name": "Zambian kwacha", "prefix": "+260", "countries": "Zambia"},
            {"code": "ZWL", "name": "Zimbabwean dollar", "prefix": "+263", "countries": "Zimbabwe"}
        ]

        for data in pays_data:
            devise = Devise.objects.create(
                nom_court=data['code'],
                nom_long=data['name'],
                pays=data['countries'],
                description=f"Devise utilisée dans {data['countries']}",
                drapeau_image=None
            )
            
            PrefixTelephone.objects.create(
                prefix=data['prefix'],
                pays=data['countries'],
                description=f"Préfixe téléphonique pour {data['countries']}",
                drapeau_image=None
            )

        services_data = [
            'Agriculture', 'Aquaculture', 'Pêche', 'Technologie', 'Immobilier',
            'Centre de marché', 'Commerce de détail', 'Commerce en gros',
            'Transport et logistique', 'Construction', 'Industrie manufacturière',
            'Services financiers', 'Tourisme et hôtellerie', 'Santé',
            'Éducation et formation', 'Énergie et utilities', 'Télécommunications',
            'Médias et divertissement', 'Consulting et services professionnels',
            'Restauration', 'Artisanat', 'Export/Import', 'Minoterie'
        ]

        services = []
        for titre in services_data:
            service = Service.objects.create(titre=titre)
            services.append(service)

        # Seed Plans (tout en MGA)
        mga = Devise.objects.get(nom_court='MGA')
        
        plans_data = [
            {
                'nom': 'freemium',
                'description': 'Plan gratuit avec fonctionnalités basiques',
                'prix': 0.00
            },
            {
                'nom': 'pro',
                'description': 'Plan professionnel avec plus de fonctionnalités',
                'prix': 25000.00  # 25 000 MGA
            },
            {
                'nom': 'max',
                'description': 'Plan maximum avec toutes les fonctionnalités',
                'prix': 75000.00  # 75 000 MGA
            }
        ]

        for plan_data in plans_data:
            Plan.objects.create(
                nom=plan_data['nom'],
                description=plan_data['description'],
                prix=plan_data['prix'],
                devise=mga
            )

        self.stdout.write(self.style.SUCCESS(f'Seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS(f'{Devise.objects.count()} devises créées'))
        self.stdout.write(self.style.SUCCESS(f'{PrefixTelephone.objects.count()} préfixes téléphoniques créés'))
        self.stdout.write(self.style.SUCCESS(f'{len(services)} services créés'))
        self.stdout.write(self.style.SUCCESS(f'{Plan.objects.count()} plans créés (tous en MGA)'))
