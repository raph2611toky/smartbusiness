from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework_simplejwt.tokens import TokenError
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.exceptions import APIException, AuthenticationFailed

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError

from datetime import timedelta, datetime
import random
import string
import os
import traceback
from uuid import uuid4
from dotenv import load_dotenv

from apps.users.serializers import UserSerializer, LoginSerializer, RegisterSerializer
from apps.users.models import User, UserOtp
from helpers.services.google.authentication import get_google_auth_url, handle_google_callback
from helpers.services.emails import envoyer_email
from helpers.helper import generate_jwt_token, enc_dec, decode_jwt_token

load_dotenv()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        tags=['Admin'],
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Connexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'nom_complet': openapi.Schema(type=openapi.TYPE_STRING),
                        'sexe': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'erreur': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'erreur': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Connecte un utilisateur avec email et mot de passe."
    )
    def post(self, request):
        try:
            print(request.data)
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'nom_complet': user.nom_complet,
                'sexe': user.sexe,
            }, status=status.HTTP_200_OK)
        except AuthenticationFailed as e:
            print(e)
            return Response({'erreur': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'erreur': f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        tags=['Admin'],
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="Inscription réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'erreur': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'erreur': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Inscription."
    )
    def post(self, request):
        try:
            print(request.data)
            if User.objects.filter(email=request.data.get('email')).exists():
                return Response({"erreur":"l'Utilisateur existe dejà"}, status=403)
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.create(serializer.validated_data)
            otp = generate_otp()
            UserOtp.objects.create(
                user=user,
                code_otp=otp,
                expirer_le=timezone.now() + timedelta(minutes=30),
                date_creation=timezone.now()
            )
            email_data = {
                'subject': 'Vérification de votre compte',
                'nom_complet': user.nom_complet,
                'code_otp': otp,
                'site_url': os.getenv('SITE_URL'),
                'current_year': datetime.now().year
            }
            try:
                envoyer_email([user.email], 'verify_email', email_data)
            except Exception as e:
                user.delete()
                return Response({'erreur': f"Erreur lors de l'envoi de l'email de vérification: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                'email': user.email,
                'message': 'Inscription réussie.'
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'erreur': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'erreur': "Cet email est déjà utilisé."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'erreur': f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleCallbackUserView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Admin'],
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY, description="Code d'authentification Google", type=openapi.TYPE_STRING),
            openapi.Parameter('state', openapi.IN_QUERY, description="État de l'authentification", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Connexion réussie via Google",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                        "access": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            201: openapi.Response(
                description="Inscription réussie via Google",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                        "access": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Gère l'authentification et l'inscription via Google OAuth."
    )
    def get(self, request):
        try:
            code = request.GET.get('code')
            state = request.GET.get('state')

            if not code or not state:
                return Response({"detail": "Code ou état manquant."}, status=status.HTTP_400_BAD_REQUEST)

            id_info = handle_google_callback(code, state)
            email = id_info.get('email')
            if not email:
                return Response({"detail": "Email non fourni par Google."}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if user:
                if not user.is_active:
                    return Response({"detail": "Compte non activé. Veuillez vérifier votre email."}, status=status.HTTP_400_BAD_REQUEST)
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Connexion réussie via Google",
                    "success": True,
                    "email": email,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }, status=status.HTTP_200_OK)

            name = id_info.get('name', 'Utilisateur Google')
            picture = id_info.get('picture', 'users/profiles/default.png')
            user = User.objects.create(
                email=email,
                nom_complet=name,
                sexe='I',
                is_verified=False,  # Require email verification
                is_active=False,
                profile=picture,
                numero_phone='',
                is_staff=False,
                is_superuser=False
            )
            try:
                otp = generate_otp()
                UserOtp.objects.create(
                    user=user,
                    code_otp=otp,
                    expirer_le=timezone.now() + timedelta(minutes=30),
                    date_creation=timezone.now()
                )
                email_data = {
                    'subject': f'Vérification de votre compte utilisateur',
                    'nom_complet': user.nom_complet,
                    'code_otp': otp,
                    'site_url': os.getenv('SITE_URL'),
                    'current_year': datetime.now().year
                }
                envoyer_email([user.email], 'verify_email', email_data)
            except Exception as e:
                user.delete()
                return Response({"detail": f"Erreur lors de la création de l'adresse, des paramètres ou de l'envoi de l'email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": f"Inscription d'utilisateur réussie via Google. Veuillez vérifier votre email pour activer votre compte.",
                "success": True,
                "email": email,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleAuthUrlView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Google Auth Redirect'],
        responses={
            200: openapi.Response(
                description="Succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "redirect_url": openapi.Schema(type=openapi.TYPE_STRING),
                        "state": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Obtenir l'URL d'authentification Google."
    )
    def get(self, request):
        try:
            redirect_url, state = get_google_auth_url()
            return Response({
                "success": True,
                "redirect_url": redirect_url,
                "state": state
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOtpView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Admin'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email de l'utilisateur"),
                'code_otp': openapi.Schema(type=openapi.TYPE_STRING, description="Code OTP")
            },
            required=['email', 'code_otp']
        ),
        responses={
            200: openapi.Response(
                description="Vérification réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides ou OTP invalide",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'erreur': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'erreur': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Vérifie le code OTP pour activer le compte utilisateur."
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            code_otp = request.data.get('code_otp')
            if not email or not code_otp:
                return Response({'erreur': "L'email et le code OTP sont requis."}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({'erreur': "Utilisateur non trouvé."}, status=status.HTTP_400_BAD_REQUEST)

            otp = UserOtp.objects.filter(user=user, code_otp=code_otp).first()
            if not otp:
                return Response({'erreur': "Code OTP invalide."}, status=status.HTTP_400_BAD_REQUEST)
            if otp.expirer_le < timezone.now():
                otp.delete()
                return Response({'erreur': "Code OTP expiré."}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.is_verified = True
            user.save()
            otp.delete()  # Remove used OTP
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Compte vérifié avec succès.',
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'erreur': f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)