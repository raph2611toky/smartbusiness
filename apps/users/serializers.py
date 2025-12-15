from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import PasswordField
from apps.users.models import User
from datetime import datetime
from helpers.geo import get_city_from_coordinates

class UserSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()
    date_naissance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nom_complet', 'email', 'date_naissance', 'profile_url', 'sexe', 'is_active', 'numero_phone']

    def get_profile_url(self, obj):
        if obj.profile and hasattr(obj.profile, 'url'):
            return f'{settings.BASE_URL}{obj.profile.url}'
        return None

    def get_date_naissance(self, obj):
        if obj.date_naissance:
            return obj.date_naissance.strftime('%d-%m-%Y')
        return None

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = PasswordField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed('Email ou mot de passe incorrect.')
        print(user.is_active)
        user.is_active = True
        user.save()
        # if not user.is_active:
        #     raise AuthenticationFailed('Compte non activé. Veuillez vérifier votre email.')

        attrs['user'] = user
        update_last_login(None, user)
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    password = PasswordField()

    class Meta:
        model = User
        fields = ['email', 'password', 'nom_complet', 'sexe', 'date_naissance', 'numero_phone']

    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Cet email est déjà utilisé."})
        validate_password(attrs.get('password'))
        if not attrs.get('nom_complet') or len(attrs.get('nom_complet')) > 100:
            raise serializers.ValidationError({"nom_complet": "Le nom complet est requis et ne peut pas dépasser 100 caractères."})
        if attrs.get('numero_phone') and len(attrs.get('numero_phone')) > 100:
            raise serializers.ValidationError({"numero_phone": "Le numéro de téléphone ne peut pas dépasser 100 caractères."})
        if attrs.get('date_naissance'):
            if attrs['date_naissance'] > timezone.now().date():
                raise serializers.ValidationError({"date_naissance": "La date de naissance ne peut pas être dans le futur."})
            if (timezone.now().date() - attrs['date_naissance']).days / 365.25 < 13:
                raise serializers.ValidationError({"date_naissance": "L'utilisateur doit avoir au moins 13 ans."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            nom_complet=validated_data['nom_complet'].capitalize(),
            email=validated_data['email'],
            sexe=validated_data.get('sexe', 'I')[0].upper(),
            date_naissance=validated_data.get('date_naissance'),
            numero_phone=validated_data.get('numero_phone', ''),
            is_superuser=False,
            is_staff=False,
            is_active=False,
            is_verified=False
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
