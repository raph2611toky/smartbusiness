from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework_simplejwt.tokens import TokenError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.request import Request
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime
from bleach.sanitizer import Cleaner
from dotenv import load_dotenv
import os
import traceback
import random
import string
from uuid import uuid4

from apps.users.serializers import UserSerializer
from apps.users.models import User, UserOtp
from helpers.services.emails import envoyer_email
from helpers.helper import generate_jwt_token, enc_dec, decode_jwt_token

load_dotenv()

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        security=[{'Bearer': []}],
        responses={
            200: UserSerializer(),
            403: openapi.Response(
                description="Accès refusé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Récupère le profil de l'utilisateur authentifié."
    )
    def get(self, request: Request):
        try:
            serializer = UserSerializer(request.user, context={'request': request})
            user = serializer.data
            if not user['is_active']:
                return Response(
                    {'error': 'Accès refusé: votre compte doit être actif. Veuillez vous connecter pour continuer.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return Response(user, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        tags=['Users'],
        security=[{'Bearer': []}],
        request_body=UserSerializer,
        responses={
            200: UserSerializer(),
            400: openapi.Response(
                description="Requête invalide",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Met à jour le profil de l'utilisateur."
    )
    def put(self, request):
        try:
            serializer = UserSerializer(instance=request.user, data=request.data, partial=True)
            if serializer.is_valid():
                user = serializer.save()
                return Response(UserSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        security=[{'Bearer': []}],
        responses={
            200: openapi.Response(
                description="Déconnexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            404: openapi.Response(
                description="Utilisateur non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        operation_description="Déconnecte l'utilisateur authentifié en désactivant son compte."
    )
    def put(self, request: Request):
        try:
            user = User.objects.get(id=request.user.id)
            user.is_active = False
            user.save()
            return Response({'message': 'Utilisateur déconnecté avec succès.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'erreur': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'erreur': f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResendOTPVerificationView(APIView):
    permission_classes = [AllowAny]

    def check_if_user_exist(self, email):
        return User.objects.filter(email=email).exists()

    def validate_data(self, data):
        try:
            keys = ['email']
            if any(key not in data.keys() for key in keys):
                return False
            return True
        except Exception:
            return False

    @swagger_auto_schema(
        tags=['Users'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email de l\'utilisateur')
            }
        ),
        responses={
            200: openapi.Response(
                description="Code OTP envoyé",
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
        operation_description="Renvoie un code OTP pour vérification du compte."
    )
    def post(self, request):
        try:
            user_data = request.data
            if not self.validate_data(user_data):
                return Response({'erreur': 'Tous les attributs sont requis'}, status=status.HTTP_400_BAD_REQUEST)

            if not self.check_if_user_exist(request.data['email']):
                return Response({'erreur': 'Email non existant'}, status=status.HTTP_400_BAD_REQUEST)

            if not User.objects.filter(email=request.data['email'], is_verified=False).exists():
                return Response({"erreur": 'Cet utilisateur a déjà un compte vérifié'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=request.data['email'], is_verified=False).first()
            code_otp = ''.join(random.choices(string.digits, k=6))
            date_expiration = timezone.now() + timedelta(minutes=30)

            UserOtp.objects.filter(user=user).delete()
            UserOtp.objects.create(code_otp=code_otp, user=user, expirer_le=date_expiration)

            data = {
                'subject': 'Vérification de votre compte Sexual AI',
                'prenom': user.nom_complet.split()[0],
                'nom': ' '.join(user.nom_complet.split()[1:]) if len(user.nom_complet.split()) > 1 else '',
                'code_otp': code_otp,
                'user_email': user.email,
                'type_utilisateur': 'vendeur' if user.is_staff else 'client',
                'verification_url': os.getenv('SITE_URL') + '/user/verify-otp/',
                'support_email': os.getenv('SUPPORT_EMAIL'),
                'site_url': os.getenv('SITE_URL'),
                'aide_url': os.getenv('AIDE_URL', os.getenv('SITE_URL') + '/aide/'),
                'confidentialite_url': os.getenv('CONFIDENTIALITE_URL', os.getenv('SITE_URL') + '/confidentialite/'),
                'current_year': datetime.now().year
            }

            envoyer_email([user.email], 'envoie_code_otp', data)

            return Response({"email": user.email, 'message': f"Un code OTP de vérification a été envoyé à {user.email}"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erreur": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserVerifyOtpView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="Vérifier le code OTP pour activer le compte utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "code_otp"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, example="utilisateur@exemple.com"),
                "code_otp": openapi.Schema(type=openapi.TYPE_STRING, example="123456")
            }
        ),
        responses={
            200: openapi.Response(
                description="Vérification réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
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
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            404: openapi.Response(
                description="Utilisateur ou OTP non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            410: openapi.Response(
                description="OTP expiré",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=["Users"]
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            code_otp = request.data.get('code_otp')

            if not email or not code_otp:
                return Response({"erreur": "Email et code OTP sont requis"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"erreur": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

            try:
                otp = UserOtp.objects.filter(user=user, code_otp=code_otp).first()
                if not otp:
                    return Response({"erreur": "Code OTP invalide"}, status=status.HTTP_400_BAD_REQUEST)
            except UserOtp.DoesNotExist:
                return Response({"erreur": "Code OTP invalide"}, status=status.HTTP_400_BAD_REQUEST)

            if otp.expirer_le < timezone.now():
                otp.delete()
                return Response({"erreur": "Code OTP expiré"}, status=status.HTTP_410_GONE)

            user.is_verified = True
            user.is_active = True
            user.save()
            UserOtp.objects.filter(user=user).delete()

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Compte vérifié avec succès",
                "email": email,
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erreur": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserMotDePasseOublieView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Envoyer un email de réinitialisation du mot de passe utilisateur",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, example="user@exemple.com")
            }
        ),
        responses={
            200: openapi.Response(
                description="Email envoyé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=["Users"]
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({"erreur": "Email requis"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"erreur": "Utilisateur introuvable"}, status=status.HTTP_400_BAD_REQUEST)

            token = generate_jwt_token({enc_dec("user_id"): enc_dec(str(user.id))})
            lien = os.getenv('SITE_URL') + f"/user/reset-password?token={token}"

            envoyer_email([email], "reinitialiser_mot_de_passe", {
                "subject": "Réinitialisation de votre mot de passe",
                "nom_utilisateur": user.nom_complet,
                "lien_reinitialisation": lien,
                "support_email": os.getenv('SUPPORT_EMAIL'),
                "site_url": os.getenv('SITE_URL'),
                "aide_url": os.getenv('AIDE_URL', os.getenv('SITE_URL') + '/aide/'),
                "confidentialite_url": os.getenv('CONFIDENTIALITE_URL', os.getenv('SITE_URL') + '/confidentialite/'),
                "current_year": datetime.now().year
            })

            return Response({"message": "Email de réinitialisation envoyé"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"erreur": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserResetPasswordView(APIView):
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
                    properties={"message": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            404: openapi.Response(
                description="Utilisateur introuvable",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"erreur": openapi.Schema(type=openapi.TYPE_STRING)}
                )
            )
        },
        tags=["Users"]
    )
    def post(self, request):
        try:
            token = request.data.get("token")
            nouveau_mot_de_passe = request.data.get("nouveau_mot_de_passe")
            if not token or not nouveau_mot_de_passe:
                return Response({"erreur": "Token et nouveau mot de passe requis"}, status=status.HTTP_400_BAD_REQUEST)

            payload = decode_jwt_token(token)
            user_id = int(enc_dec(payload.get(enc_dec("user_id", "d")), 'd'))

            user = User.objects.get(id=user_id)
            user.set_password(nouveau_mot_de_passe)
            user.save()

            return Response({"message": "Mot de passe réinitialisé avec succès"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"erreur": "Utilisateur introuvable"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"erreur": f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ContactSupportView(APIView):
    permission_classes = [AllowAny]

    def validate_data(self, data):
        required_keys = ['nom_complet', 'adresse_email', 'message']
        if not all(key in data for key in required_keys):
            return False, {'erreur': 'Tous les champs (nom_complet, adresse_email, message) sont requis'}

        validator = EmailValidator()
        try:
            validator(data['adresse_email'])
        except ValidationError:
            return False, {'erreur': 'Adresse email invalide'}

        if not data['nom_complet'].strip() or len(data['nom_complet']) > 100:
            return False, {'erreur': 'Le nom complet doit être non vide et inférieur à 100 caractères'}

        if not data['message'].strip() or len(data['message']) > 1000:
            return False, {'erreur': 'Le message doit être non vide et inférieur à 1000 caractères'}

        return True, None

    def sanitize_message(self, message):
        cleaner = Cleaner(
            tags=['p', 'br', 'strong', 'em'],
            attributes={},
            strip=True
        )
        return cleaner.clean(message)

    @swagger_auto_schema(
        tags=['Support'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'nom_complet': openapi.Schema(type=openapi.TYPE_STRING, description='Nom complet de l\'utilisateur'),
                'adresse_email': openapi.Schema(type=openapi.TYPE_STRING, description='Adresse email de l\'utilisateur'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message de l\'utilisateur'),
            },
            required=['nom_complet', 'adresse_email', 'message']
        ),
        responses={
            200: openapi.Response(
                description="Message envoyé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
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
        operation_description="Envoie un message au support de Sexual AI."
    )
    def post(self, request):
        try:
            data = request.data
            is_valid, error_response = self.validate_data(data)
            if not is_valid:
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

            sanitized_message = self.sanitize_message(data['message'])

            email_data = {
                'subject': 'Nouveau message de contact - Sexual AI',
                'nom_complet': data['nom_complet'],
                'adresse_email': data['adresse_email'],
                'message': sanitized_message,
                'current_year': datetime.now().year,
                'current_date': datetime.now().strftime('%d/%m/%Y'),
                'current_time': datetime.now().strftime('%H:%M'),
                'site_url': os.getenv('SITE_URL'),
                'admin_url': os.getenv('ADMIN_URL', os.getenv('SITE_URL') + '/admin/'),
                'aide_url': os.getenv('AIDE_URL', os.getenv('SITE_URL') + '/aide/')
            }

            support_email = os.getenv('SUPPORT_EMAIL')
            envoyer_email([support_email], 'support_message', email_data)

            return Response({'message': 'Votre message a été envoyé avec succès au support.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'erreur': f"{str(e)}: {str(traceback.format_exc())}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)