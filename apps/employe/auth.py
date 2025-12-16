from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.exceptions import TokenError

from django.contrib.auth.hashers import check_password
from django.utils import timezone
from datetime import datetime, timedelta
import os, traceback, random, string
from dotenv import load_dotenv

from apps.employe.models import Employe, EmployeOtp, EmployeCompte, Profession, EmployeOutstandingToken
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from apps.entreprise.permissions import IsAuthenticatedEntreprise
from apps.employe.serializers import EmployeCreateSerializer
from apps.employe.tokens import EmployeRefreshToken

from apps.employe.permissions import IsAuthenticatedEmploye
from helpers.services.emails import envoyer_email
from helpers.helper import generate_jwt_token, enc_dec, decode_jwt_token

load_dotenv()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


class EmployeLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'mot_de_passe': openapi.Schema(type=openapi.TYPE_STRING),
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
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'nom_complet': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(...),
            401: openapi.Response(...),
            500: openapi.Response(...),
        },
        operation_description="Connexion employé avec email et mot de passe."
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            mot_de_passe = request.data.get('mot_de_passe')

            if not email or not mot_de_passe:
                return Response({
                    'message': "Email et mot de passe sont requis.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            employe = Employe.objects.filter(email=email).first()
            if not employe or not employe.est_actif:
                return Response({
                    'message': "Email ou mot de passe incorrect.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                compte = EmployeCompte.objects.get(employe=employe, est_actif=True)
            except EmployeCompte.DoesNotExist:
                return Response({
                    'message': "Compte employé inactif ou inexistant.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not compte.check_password(mot_de_passe):
                compte.nombre_tentatives += 1
                compte.save()
                return Response({
                    'message': "Email ou mot de passe incorrect.",
                    'success': False,
                    'donnees': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            refresh = EmployeRefreshToken.for_employe(employe)

            return Response({
                'message': "Connexion réussie",
                'success': True,
                'donnees': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'nom_complet': employe.nom_complet,
                    'email': employe.email
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeCreateByEntrepriseView(APIView):
    permission_classes = [IsAuthenticatedEntreprise]
    parser_classes = [FormParser, MultiPartParser]

    @swagger_auto_schema(
        tags=['Employé'],
        manual_parameters=[
            openapi.Parameter('nom_complet', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('fonction', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('profession', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False,
                              description="ID de la profession (obligatoire si est_un_compte=True)"),
            openapi.Parameter('est_un_compte', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
        ],
        responses={201: openapi.Response(...), 400: openapi.Response(...), 500: openapi.Response(...)},
        operation_description="Création d’un employé par l’entreprise, avec ou sans compte."
    )
    def post(self, request):
        try:
            serializer = EmployeCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            employe = serializer.save(entreprise=request.entreprise)

            if employe.est_un_compte and employe.profession:
                # lien set-password
                payload = {
                    "employe_email": enc_dec(employe.email),
                    "profession_id": enc_dec(str(employe.profession.id)),
                    "entreprise_id": enc_dec(str(request.entreprise.id)),
                }
                token = generate_jwt_token(payload)
                lien = os.getenv('FRONTEND_URL_DEV') + f"/employe/set-password?token={token}"

                envoyer_email(
                    [employe.email],
                    "employe_set_password",
                    {
                        "subject": "Activation de votre compte employé",
                        "nom_complet": employe.nom_complet,
                        "entreprise": request.entreprise.nom_complet,
                        "lien_activation": lien,
                    }
                )
                type_invite = "COMPTE"
            else:
                # simple OTP
                otp = generate_otp()
                EmployeOtp.objects.create(
                    employe=employe,
                    code_otp=otp,
                    date_expiration=timezone.now() + timedelta(minutes=30)
                )
                envoyer_email(
                    [employe.email],
                    "employe_confirmation",
                    {
                        "subject": "Confirmation de votre email employé",
                        "nom_complet": employe.nom_complet,
                        "code_otp": otp,
                        "entreprise": request.entreprise.nom_complet,
                    }
                )
                type_invite = "OTP"

            return Response({
                "message": "Employé créé avec succès.",
                "success": True,
                "donnees": {
                    "employe_id": employe.id,
                    "email": employe.email,
                    "type_invitation": type_invite
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "message": f"Erreur serveur: {str(e)}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeSetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Employé'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "token": openapi.Schema(type=openapi.TYPE_STRING),
                "mot_de_passe": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["token", "mot_de_passe"]
        ),
        responses={200: openapi.Response(...), 400: openapi.Response(...), 500: openapi.Response(...)},
        operation_description="Définir le mot de passe lors de la première activation du compte employé."
    )
    def post(self, request):
        try:
            token = request.data.get("token")
            mot_de_passe = request.data.get("mot_de_passe")

            if not token or not mot_de_passe:
                return Response({
                    "message": "Token et mot de passe sont requis.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            payload = decode_jwt_token(token)
            email = enc_dec(payload.get("employe_email"), 'd')
            profession_id = int(enc_dec(payload.get("profession_id"), 'd'))

            employe = Employe.objects.get(email=email)
            profession = Profession.objects.get(id=profession_id)

            compte, _ = EmployeCompte.objects.get_or_create(employe=employe)
            compte.set_password(mot_de_passe)
            compte.est_actif = True
            compte.save()

            employe.profession = profession
            employe.est_verifie = True
            employe.est_actif = True
            employe.est_un_compte = True
            employe.save()

            refresh = EmployeRefreshToken.for_employe(employe)
            return Response({
                "message": "Mot de passe défini, compte activé.",
                "success": True,
                "donnees": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Erreur: {str(e)}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeConfirmOtpView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Employé'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "code_otp": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["email", "code_otp"]
        ),
        responses={200: openapi.Response(...), 400: openapi.Response(...), 500: openapi.Response(...)},
        operation_description="Confirmer l'email d'un employé (sans compte) via OTP."
    )
    def post(self, request):
        try:
            email = request.data.get("email")
            code_otp = request.data.get("code_otp")

            if not email or not code_otp:
                return Response({
                    "message": "Email et code OTP sont requis.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            employe = Employe.objects.filter(email=email).first()
            if not employe:
                return Response({
                    "message": "Employé introuvable.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            otp = EmployeOtp.objects.filter(employe=employe, code_otp=code_otp).first()
            if not otp:
                return Response({
                    "message": "Code OTP invalide.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            if otp.date_expiration < timezone.now():
                otp.delete()
                return Response({
                    "message": "Code OTP expiré.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            employe.est_verifie = True
            employe.save()
            otp.utilise = True
            otp.save()

            return Response({
                "message": "Email employé vérifié avec succès.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Erreur serveur: {str(e)}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé - Auth'],
        operation_description="Envoyer un email de réinitialisation du mot de passe employé (uniquement pour les employés ayant un compte).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, example="employe@exemple.com")
            }
        ),
        responses={
            200: openapi.Response(
                description="Email envoyé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Requête invalide",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            email = request.data.get("email")
            if not email:
                return Response({
                    "message": "Email requis.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            employe = Employe.objects.filter(email=email).first()
            if not employe:
                # réponse neutre (évite fuite d'info)
                return Response({
                    "message": "Si l'email existe, un lien de réinitialisation a été envoyé.",
                    "success": True,
                    "donnees": {}
                }, status=status.HTTP_200_OK)

            compte = EmployeCompte.objects.filter(employe=employe, est_actif=True).first()
            if not compte:
                return Response({
                    "message": "Cet employé n'a pas de compte actif.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            token = generate_jwt_token({
                "employe_id": enc_dec(str(employe.id)),
            }, expires_in_minutes=60)

            lien = os.getenv("FRONTEND_URL_DEV", "").rstrip("/") + f"/employe/reset-password?token={token}"

            envoyer_email([email], "employe_reset_password", {
                "subject": "Réinitialisation de votre mot de passe",
                "nom_complet": employe.nom_complet,
                "entreprise": employe.entreprise.nom_complet,
                "lien_reinitialisation": lien,
                "current_year": datetime.now().year
            })

            return Response({
                "message": "Si l'email existe, un lien de réinitialisation a été envoyé.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé - Auth'],
        operation_description="Réinitialiser le mot de passe employé via token (reçu par email).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token", "nouveau_mot_de_passe"],
            properties={
                "token": openapi.Schema(type=openapi.TYPE_STRING),
                "nouveau_mot_de_passe": openapi.Schema(type=openapi.TYPE_STRING, example="NouveauMdp@123")
            }
        ),
        responses={
            200: openapi.Response(
                description="Mot de passe réinitialisé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Token invalide / données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: openapi.Response(
                description="Employé introuvable",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            token = request.data.get("token")
            nouveau_mot_de_passe = request.data.get("nouveau_mot_de_passe")

            if not token or not nouveau_mot_de_passe:
                return Response({
                    "message": "Token et nouveau mot de passe requis.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            payload = decode_jwt_token(token)
            employe_id = int(enc_dec(payload.get("employe_id"), "d"))

            employe = Employe.objects.filter(id=employe_id).first()
            if not employe:
                return Response({
                    "message": "Employé introuvable.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_404_NOT_FOUND)

            compte = EmployeCompte.objects.filter(employe=employe).first()
            if not compte:
                return Response({
                    "message": "Compte employé inexistant.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            compte.set_password(nouveau_mot_de_passe)
            compte.est_actif = True
            compte.nombre_tentatives = 0
            compte.bloque_jusqua = None
            compte.save()

            return Response({
                "message": "Mot de passe réinitialisé avec succès.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_400_BAD_REQUEST)


class EmployeLogoutView(APIView):
    permission_classes = [IsAuthenticatedEmploye]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé - Auth'],
        operation_description="Déconnexion employé (blacklist du refresh token).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token JWT")
            }
        ),
        responses={
            200: openapi.Response(
                description="Déconnexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Refresh token invalide/manquant",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            )
        }
    )
    def put(self, request):
        try:
            refresh_str = request.data.get("refresh")
            if not refresh_str:
                return Response({
                    "message": "Refresh token requis.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                refresh = EmployeRefreshToken(refresh_str)
                jti = str(refresh.get("jti"))
                exp_ts = int(refresh.get("exp"))
            except TokenError:
                return Response({
                    "message": "Refresh token invalide.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Enregistrer / blacklister côté DB (compat avec ton modèle)
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.get_current_timezone())
            EmployeOutstandingToken.objects.update_or_create(
                jti=jti,
                defaults={
                    "employe": request.employe,
                    "token": refresh_str,
                    "date_expiration": expires_at,
                    "est_blackliste": True
                }
            )

            # journaliser dernier login si besoin
            try:
                compte = request.employe.compte
                compte.dernier_login = timezone.now()
                compte.save()
            except Exception:
                pass

            return Response({
                "message": "Déconnexion réussie.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
