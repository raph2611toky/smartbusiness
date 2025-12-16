# apps/entreprise/serializers.py - Section Employé
from rest_framework import serializers
from django.conf import settings
from datetime import datetime
from apps.employe.models import (
    Employe, EmployeCompte, EmployeOtp, Profession, Acces, PrefixTelephone
)
from apps.entreprise.serializers import PrefixTelephoneSerializer

class AccesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acces
        fields = ['id', 'titre', 'description', 'permissions']

class ProfessionSerializer(serializers.ModelSerializer):
    acces_list = AccesSerializer(source='acces', many=True, read_only=True)
    
    class Meta:
        model = Profession
        fields = ['id', 'nom', 'description', 'couleur', 'acces_list']

class EmployeCompteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeCompte
        fields = ['id', 'est_actif', 'dernier_login', 'nombre_tentatives']
        read_only_fields = ['id']

class EmployeOtpSerializer(serializers.ModelSerializer):
    date_creation_formatted = serializers.SerializerMethodField()
    date_expiration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeOtp
        fields = ['id', 'code_otp', 'date_creation_formatted', 'date_expiration_formatted']
    
    def get_date_creation_formatted(self, obj):
        return datetime.strftime(obj.date_creation, '%d/%m/%Y %H:%M')
    
    def get_date_expiration_formatted(self, obj):
        return datetime.strftime(obj.date_expiration, '%d/%m/%Y %H:%M')

class EmployeListSerializer(serializers.ModelSerializer):
    profession_data = ProfessionSerializer(source='compte.profession', read_only=True)
    prefix_telephone_data = PrefixTelephoneSerializer(source='prefix_telephone', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Employe
        fields = [
            'id', 'nom_complet', 'email', 'fonction', 'est_actif', 'est_verifie',
            'est_un_compte', 'photo_url', 'profession_data', 'prefix_telephone_data',
            'date_creation', 'date_embauche'
        ]
    
    def get_photo_url(self, obj):
        if getattr(obj, 'photo', None):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
        return None

class EmployeCreateSerializer(serializers.ModelSerializer):
    # profession = serializers.PrimaryKeyRelatedField(queryset=Profession.objects.all(), required=False)
    prefix_telephone = serializers.PrimaryKeyRelatedField(
        queryset=PrefixTelephone.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = Employe
        fields = [
            'nom_complet', 'email', 'date_naissance', 'cin', 'prefix_telephone',
            'numero_telephone', 'adresse', 'etat_civil', 'fonction', 'photo', 'est_un_compte'#, 'profession'
        ]
    
    def validate(self, attrs):
        if attrs.get('est_un_compte') and not attrs.get('profession'):
            raise serializers.ValidationError("Une profession est requise pour créer un compte employé.")
        return attrs
    
    def validate_email(self, value):
        if Employe.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_cin(self, value):
        request = self.context.get('request')
        entreprise = request.entreprise if hasattr(request, 'entreprise') else None
        if entreprise and Employe.objects.filter(
            entreprise=entreprise, cin=value
        ).exists():
            raise serializers.ValidationError("Ce CIN est déjà utilisé dans cette entreprise.")
        return value
    
    def create(self, validated_data):
        profession = validated_data.pop('profession', None)  # Pop extra field
        instance = super().create(validated_data)
        if profession and validated_data.get('est_un_compte'):
            compte = EmployeCompte.objects.create(employe=instance, profession=profession)
        return instance

class EmployeProfileUpdateSerializer(serializers.ModelSerializer):
    profession = serializers.PrimaryKeyRelatedField(queryset=Profession.objects.all(), required=False)
    
    class Meta:
        model = Employe
        fields = [
            'nom_complet', 'date_naissance', 'numero_telephone', 'adresse',
            'etat_civil', 'fonction', 'photo', 'profession'
        ]

# Supprime ces lignes ou remplace par :
class EmployeSerializer(serializers.ModelSerializer):
    profession_data = ProfessionSerializer(read_only=True)
    prefix_telephone_data = PrefixTelephoneSerializer(source='prefix_telephone', read_only=True)
    photo_url = serializers.SerializerMethodField()
    compte = EmployeCompteSerializer(read_only=True)
    
    class Meta:
        model = Employe
        fields = '__all__'  # ou liste explicite
    
    def get_photo_url(self, obj):
        if getattr(obj, 'photo', None):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
        return None
