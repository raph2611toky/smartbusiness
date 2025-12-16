from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException, AuthenticationFailed

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password

from datetime import timedelta, datetime
import random
import string
import os
import traceback
from dotenv import load_dotenv

from apps.entreprise.tokens import EntrepriseRefreshToken
from apps.entreprise.serializers import EntrepriseSerializer
from apps.entreprise.models import Entreprise, EntrepriseOtp, Plan

from helpers.services.google.authentication import handle_google_callback
from helpers.services.emails import envoyer_email
from helpers.helper import generate_jwt_token, enc_dec, decode_jwt_token

load_dotenv()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

class EntrepriseLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Entreprise'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'mot_de_passe': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'mot_de_passe']
        ),
        responses={
            200: openapi.Response(
                description="Connexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'nom_complet': openapi.Schema(type=openapi.TYPE_STRING),
                                'type_entreprise': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Identifiants invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            401: openapi.Response(
                description="Compte non vérifié/activé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        operation_description="Connecte une entreprise avec email et mot de passe."
    )
    def post(self, request):
        try:
            print("Login request:", request.data)
            email = request.data.get('email')
            mot_de_passe = request.data.get('mot_de_passe')

            if not email or not mot_de_passe:
                return Response({
                    'message': "Email et mot de passe sont requis.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # 1. Vérifier si l'entreprise existe
            try:
                entreprise = Entreprise.objects.get(email=email)
            except Entreprise.DoesNotExist:
                return Response({
                    'message': "Email ou mot de passe incorrect.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # 2. Vérifier si le compte est actif et vérifié
            if not entreprise.est_verifie:
                return Response({
                    'message': "Votre compte n'est pas encore vérifié. Vérifiez votre email.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_401_UNAUTHORIZED)

            # 3. Vérifier le mot de passe
            if not entreprise.check_password(mot_de_passe):
                return Response({
                    'message': "Email ou mot de passe incorrect.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # 4. Générer les tokens
            refresh = EntrepriseRefreshToken.for_entreprise(entreprise)
            
            return Response({
                'message': 'Connexion réussie',
                'success': True,
                'donnees': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'nom_complet': entreprise.nom_complet,
                    'type_entreprise': entreprise.get_type_entreprise_display(),
                    'email': entreprise.email
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EntrepriseRegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [FormParser, MultiPartParser]

    @swagger_auto_schema(
        tags=['Entreprise'],
        request_body=EntrepriseSerializer,
        responses={
            201: openapi.Response(
                description="Inscription réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            409: openapi.Response(
                description="Entreprise existe déjà",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        operation_description="Inscription d'une nouvelle entreprise."
    )
    def post(self, request):
        try:
            print(request.data)
            if Entreprise.objects.filter(email=request.data.get('email')).exists():
                return Response({
                    'message': "L'entreprise existe déjà",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_409_CONFLICT)
                
            plan_freenium, _ = Plan.objects.get_or_create(nom='freemium',defaults={'description': 'Plan gratuit avec fonctionnalités basiques','prix': 0.00})
            data = request.data
            data['plan'] = request.data.get('plan', plan_freenium.id)
            serializer = EntrepriseSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            entreprise = serializer.save()
            
            otp = generate_otp()
            EntrepriseOtp.objects.create(
                entreprise=entreprise,
                code_otp=otp,
                date_expiration=timezone.now() + timedelta(minutes=30),
                date_creation=timezone.now()
            )
            
            email_data = {
                'subject': 'Vérification de votre compte entreprise',
                'nom_complet': entreprise.nom_complet,
                'code_otp': otp,
                'site_url': os.getenv('SITE_URL')+f"/verification-otp-entreprise/?email={entreprise.email}",
                'current_year': datetime.now().year
            }
            
            envoyer_email([entreprise.email], 'verify_email_entreprise', email_data)
            
            return Response({
                'message': 'Inscription réussie. Vérifiez votre email.',
                'success': True,
                'donnees': {'email': entreprise.email}
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'message': str(e),
                'success': False,
                'donnees': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({
                'message': "Cet email est déjà utilisé.",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': f"{str(e)}: {str(traceback.format_exc())}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleCallbackEntrepriseView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Entreprise'],
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
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'access': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            201: openapi.Response(
                description="Inscription réussie via Google",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'access': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
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
                return Response({
                    'message': "Code ou état manquant.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            id_info = handle_google_callback(code, state)
            email = id_info.get('email')
            if not email:
                return Response({
                    'message': "Email non fourni par Google.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            entreprise = Entreprise.objects.filter(email=email).first()
            if entreprise:
                if not entreprise.est_actif or not entreprise.est_verifie:
                    return Response({
                        'message': "Compte non activé. Veuillez vérifier votre email.",
                        'success': False,
                        'donnees': {}
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                refresh = EntrepriseRefreshToken.for_entreprise(entreprise)
                return Response({
                    'message': "Connexion réussie via Google",
                    'success': True,
                    'donnees': {
                        'email': email,
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    }
                }, status=status.HTTP_200_OK)

            # Création nouvelle entreprise via Google
            name = id_info.get('name', 'Entreprise Google')
            mot_de_passe = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            nif_stat = f'NIF-{random.randint(1000000, 9999999)}'
            
            entreprise_data = {
                'nom_complet': name,
                'email': email,
                'mot_de_passe': mot_de_passe,
                'type_entreprise': 'AUTRE',
                'nif_stat': nif_stat,
                'est_verifie': False,
                'est_actif': False
            }
            
            serializer = EntrepriseSerializer(data=entreprise_data)
            serializer.is_valid(raise_exception=True)
            entreprise = serializer.save()
            
            otp = generate_otp()
            EntrepriseOtp.objects.create(
                entreprise=entreprise,
                code_otp=otp,
                date_expiration=timezone.now() + timedelta(minutes=30),
                date_creation=timezone.now()
            )
            
            email_data = {
                'subject': 'Vérification de votre compte entreprise',
                'nom_complet': entreprise.nom_complet,
                'code_otp': otp,
                'site_url': os.getenv('SITE_URL'),
                'current_year': datetime.now().year
            }
            
            envoyer_email([entreprise.email], 'verify_email_entreprise', email_data)
            
            refresh = EntrepriseRefreshToken.for_entreprise(entreprise)
            return Response({
                'message': "Inscription réussie via Google. Vérifiez votre email pour activer votre compte.",
                'success': True,
                'donnees': {
                    'email': email,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'message': f"{str(e)}: {str(traceback.format_exc())}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyEntrepriseOtpView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Entreprise'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email de l'entreprise"),
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
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides ou OTP invalide",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        operation_description="Vérifie le code OTP pour activer le compte entreprise."
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            code_otp = request.data.get('code_otp')
            
            if not email or not code_otp:
                return Response({
                    'message': "L'email et le code OTP sont requis.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            entreprise = Entreprise.objects.filter(email=email).first()
            if not entreprise:
                return Response({
                    'message': "Entreprise non trouvée.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            otp = EntrepriseOtp.objects.filter(
                entreprise=entreprise, 
                code_otp=code_otp
            ).first()
            
            if not otp:
                return Response({
                    'message': "Code OTP invalide.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if otp.date_expiration < timezone.now():
                otp.delete()
                return Response({
                    'message': "Code OTP expiré.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Activation
            entreprise.est_actif = True
            entreprise.est_verifie = True
            entreprise.save()
            otp.delete()
            
            refresh = EntrepriseRefreshToken.for_entreprise(entreprise)
            return Response({
                'message': 'Compte entreprise vérifié avec succès.',
                'success': True,
                'donnees': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message': f"{str(e)}: {str(traceback.format_exc())}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EntrepriseMotDePasseOublieView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Envoyer un email de réinitialisation du mot de passe entreprise",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, example="entreprise@exemple.com")
            }
        ),
        responses={
            200: openapi.Response(
                description="Email envoyé", 
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Erreur", 
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        tags=["Entreprise"]
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({
                    'message': "Email requis",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            entreprise = Entreprise.objects.filter(email=email).first()
            if not entreprise:
                return Response({
                    'message': "Entreprise introuvable",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            token = generate_jwt_token({"entreprise_id": enc_dec(str(entreprise.id))})
            lien = os.getenv('FRONTEND_URL_DEV') + f"/entreprise/reset-password?token={token}"

            envoyer_email([email], "reinitialiser_mot_de_passe_entreprise", {
                "subject": "Réinitialisation de votre mot de passe",
                "nom_entreprise": entreprise.nom_complet,
                "lien_reinitialisation": lien
            })

            return Response({
                'message': "Email de réinitialisation envoyé",
                'success': True,
                'donnees': {}
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message': str(e),
                'success': False,
                'donnees': {}
            }, status=status.HTTP_400_BAD_REQUEST)

class EntrepriseResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Réinitialiser le mot de passe avec le token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token", "nouveau_mot_de_passe"],
            properties={
                "token": openapi.Schema(type=openapi.TYPE_STRING),
                "nouveau_mot_de_passe": openapi.Schema(type=openapi.TYPE_STRING, example="nouveaumotdepasse123")
            }
        ),
        responses={
            200: openapi.Response(
                description="Mot de passe réinitialisé", 
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Erreur", 
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: openapi.Response(
                description="Entreprise introuvable", 
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        tags=["Entreprise"]
    )
    def post(self, request):
        try:
            token = request.data.get("token")
            nouveau_mot_de_passe = request.data.get("nouveau_mot_de_passe")
            payload = decode_jwt_token(token)
            entreprise_id = int(enc_dec(payload.get("entreprise_id"), 'd'))

            entreprise = Entreprise.objects.get(id=entreprise_id)
            entreprise.mot_de_passe = make_password(nouveau_mot_de_passe)
            entreprise.save()

            return Response({
                'message': "Mot de passe réinitialisé avec succès",
                'success': True,
                'donnees': {}
            }, status=status.HTTP_200_OK)

        except Entreprise.DoesNotExist:
            return Response({
                'message': "Entreprise introuvable",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'message': str(e),
                'success': False,
                'donnees': {}
            }, status=status.HTTP_400_BAD_REQUEST)

class ResendEntrepriseOtpView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Entreprise'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Email de l'entreprise",
                    example="entreprise@exemple.com"
                )
            },
            required=['email']
        ),
        responses={
            200: openapi.Response(
                description="OTP renvoyé avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'nouvel_otp_envoye': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                                'expires_in_minutes': openapi.Schema(type=openapi.TYPE_INTEGER, default=30)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Entreprise non trouvée ou déjà vérifiée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            429: openapi.Response(
                description="Trop de demandes récentes",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'attendre_minutes': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        },
        operation_description="Renvoyer un nouveau code OTP de vérification pour une entreprise."
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({
                    'message': "L'email est requis.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier si l'entreprise existe
            entreprise = Entreprise.objects.filter(email=email).first()
            if not entreprise:
                return Response({
                    'message': "Entreprise non trouvée.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier si déjà vérifiée
            if entreprise.est_verifie and entreprise.est_actif:
                return Response({
                    'message': "Votre compte est déjà vérifié et activé.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Rate limiting: vérifier les OTP récents (5 min cooldown)
            otp_recent = EntrepriseOtp.objects.filter(
                entreprise=entreprise,
                date_creation__gte=timezone.now() - timedelta(minutes=5)
            ).first()
            
            if otp_recent:
                minutes_restants = 5 - int((timezone.now() - otp_recent.date_creation).total_seconds() / 60)
                return Response({
                    'message': "Trop de demandes récentes. Veuillez patienter.",
                    'success': False,
                    'donnees': {
                        'attendre_minutes': max(1, minutes_restants)
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Supprimer les anciens OTP non expirés pour ce compte
            EntrepriseOtp.objects.filter(
                entreprise=entreprise,
                date_expiration__gte=timezone.now()
            ).delete()

            # Générer et envoyer nouveau OTP
            otp = generate_otp()
            nouveau_otp = EntrepriseOtp.objects.create(
                entreprise=entreprise,
                code_otp=otp,
                date_expiration=timezone.now() + timedelta(minutes=30),
                date_creation=timezone.now()
            )

            email_data = {
                'subject': 'Nouveau code de vérification - Compte Entreprise',
                'nom_complet': entreprise.nom_complet,
                'code_otp': otp,
                'site_url': os.getenv('SITE_URL'),
                'current_year': datetime.now().year
            }

            # Envoyer email avec gestion d'erreur
            try:
                envoyer_email([entreprise.email], 'verify_email_entreprise', email_data)
            except Exception as email_error:
                # Nettoyer l'OTP en cas d'erreur email
                nouveau_otp.delete()
                return Response({
                    'message': f"Erreur lors de l'envoi de l'email: {str(email_error)}",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'message': 'Nouveau code OTP envoyé avec succès.',
                'success': True,
                'donnees': {
                    'email': entreprise.email,
                    'nouvel_otp_envoye': True,
                    'expires_in_minutes': 30
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message': f"Erreur serveur: {str(e)} - {str(traceback.format_exc())}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
