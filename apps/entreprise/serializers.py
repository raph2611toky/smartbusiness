# apps/entreprise/serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.conf import settings
from datetime import datetime
from .models import Devise, PrefixTelephone, Plan, Service, Entreprise, EntrepriseOtp, EntrepriseOutstandingToken

class DeviseSerializer(serializers.ModelSerializer):
    drapeau_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Devise
        fields = ['id', 'nom_court', 'nom_long', 'description', 'pays', 'drapeau_image_url']
        read_only_fields = ['id']

    def get_drapeau_image_url(self, obj):
        return f'http://{settings.BASE_URL}/media/{obj.drapeau_image}' if obj.drapeau_image else None

    def validate_nom_court(self, value):
        if Devise.objects.filter(nom_court=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ce nom court de devise est déjà utilisé.")
        return value

class PrefixTelephoneSerializer(serializers.ModelSerializer):
    drapeau_image_url = serializers.SerializerMethodField()

    class Meta:
        model = PrefixTelephone
        fields = ['id', 'prefix', 'description', 'pays', 'drapeau_image_url']
        read_only_fields = ['id']

    def get_drapeau_image_url(self, obj):
        return f'http://{settings.BASE_URL}/media/{obj.drapeau_image}' if obj.drapeau_image else None

    def validate_prefix(self, value):
        if PrefixTelephone.objects.filter(prefix=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ce préfixe téléphonique est déjà utilisé.")
        return value

class PlanSerializer(serializers.ModelSerializer):
    devise = serializers.PrimaryKeyRelatedField(queryset=Devise.objects.all(), allow_null=True)

    class Meta:
        model = Plan
        fields = ['id', 'nom', 'description', 'prix', 'devise']
        read_only_fields = ['id']

    def validate_nom(self, value):
        if Plan.objects.filter(nom=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ce nom de plan est déjà utilisé.")
        return value

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'titre']
        read_only_fields = ['id']

class EntrepriseSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    date_creation = serializers.SerializerMethodField()
    services = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Liste des noms de services (ex: ['Comptabilité', 'RH', 'IT']) - Créés automatiquement si inexistants"
    )
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), allow_null=True)
    prefix_telephone = serializers.SerializerMethodField()

    class Meta:
        model = Entreprise
        fields = [
            'id', 'nom_complet', 'description', 'email', 'mot_de_passe', 'nif_stat',
            'date_creation', 'profile_url', 'prefix_telephone', 'numero_telephone', 'est_verifie',
            'est_actif', 'services', 'plan', 'user_type', 'type_entreprise'
        ]
        read_only_fields = ['id', 'date_creation', 'est_verifie', 'user_type']
        extra_kwargs = {
            'mot_de_passe': {'write_only': True}
        }

    def get_profile_url(self, obj):
        return f'http://{settings.BASE_URL}/media/{obj.profile}' if obj.profile else None

    def get_user_type(self, obj):
        return "ENTREPRISE"

    def get_date_creation(self, obj):
        if obj.date_creation:
            return datetime.strftime(obj.date_creation, "%d-%m-%Y")
        return None
    
    def get_prefix_telephone(self, obj):
        return obj.prefix_telephone.prefix

    def validate_email(self, value):
        if Entreprise.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        services_data = validated_data.pop('services', [])
        plan_data = validated_data.pop('plan', None)
        prefix_data = validated_data.pop('prefix_telephone', None)
        validated_data['mot_de_passe'] = make_password(validated_data['mot_de_passe'])
        instance = super().create(validated_data)
        services_crees = []
        for service_nom in services_data:
            service_nom = service_nom.strip().title()
            service, created = Service.objects.get_or_create(
                titre=service_nom,
                defaults={'titre': service_nom}
            )
            instance.services.add(service)
            services_crees.append({
                'nom': service.titre,
                'existant': not created,
                'id': service.id
            })
        if plan_data:
            instance.plan = plan_data
        if prefix_data:
            instance.prefix_telephone = prefix_data
        instance.save()
        instance.services_list = services_crees
        return instance

    def update(self, instance, validated_data):
        services_data = validated_data.pop('services', None)
        plan_data = validated_data.pop('plan', None)
        prefix_data = validated_data.pop('prefix_telephone', None)
        if 'mot_de_passe' in validated_data:
            validated_data['mot_de_passe'] = make_password(validated_data['mot_de_passe'])
        instance = super().update(instance, validated_data)
        if services_data is not None:
            instance.services.set(services_data)
        if plan_data is not None:
            instance.plan = plan_data
        if prefix_data is not None:
            instance.prefix_telephone = prefix_data
        instance.save()
        return instance

class EntrepriseOtpSerializer(serializers.ModelSerializer):
    date_creation = serializers.SerializerMethodField()
    date_expiration = serializers.SerializerMethodField()

    class Meta:
        model = EntrepriseOtp
        fields = ['id', 'code_otp', 'entreprise', 'date_expiration', 'date_creation']
        read_only_fields = ['id', 'date_creation']

    def get_date_creation(self, obj):
        return datetime.strftime(obj.date_creation, "%d-%m-%Y %H:%M:%S")

    def get_date_expiration(self, obj):
        return datetime.strftime(obj.date_expiration, "%d-%m-%Y %H:%M:%S")

class EntrepriseOutstandingTokenSerializer(serializers.ModelSerializer):
    date_creation = serializers.SerializerMethodField()
    date_expiration = serializers.SerializerMethodField()

    class Meta:
        model = EntrepriseOutstandingToken
        fields = ['id', 'entreprise', 'jti', 'token', 'date_creation', 'date_expiration', 'est_blackliste']
        read_only_fields = ['id', 'date_creation']

    def get_date_creation(self, obj):
        return datetime.strftime(obj.date_creation, "%d-%m-%Y %H:%M:%S")

    def get_date_expiration(self, obj):
        return datetime.strftime(obj.date_expiration, "%d-%m-%Y %H:%M:%S")

class EntrepriseUpdatePlanSerializer(serializers.Serializer):
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(),
        required=True,
        error_messages={
            'required': 'Le plan est requis.',
            'does_not_exist': 'Ce plan n\'existe pas.',
            'invalid': 'ID plan invalide.'
        }
    )

    def validate_plan(self, value):
        entreprise = self.context.get('entreprise')
        if not entreprise:
            raise serializers.ValidationError("Entreprise non trouvée.")
        
        return value
