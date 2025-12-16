# apps/employe/views.py
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback

from apps.entreprise.permissions import IsAuthenticatedEntreprise
from apps.employe.permissions import IsAuthenticatedEmploye

from apps.employe.models import Employe, Profession
from apps.employe.serializers import (
    ProfessionSerializer,
    EmployeListSerializer,
    EmployeProfileUpdateSerializer
)


class ProfessionListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Référence'],
        operation_description="Lister toutes les professions avec la liste des accès inclus.",
        responses={
            200: openapi.Response(
                description="Liste professions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "donnees": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                    }
                )
            ),
            500: openapi.Response(description="Erreur serveur", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "donnees": openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )),
        }
    )
    def get(self, request):
        try:
            professions = Profession.objects.prefetch_related('acces').all().order_by('nom')
            serializer = ProfessionSerializer(professions, many=True)
            return Response({
                "message": "Liste des professions récupérée avec succès.",
                "success": True,
                "donnees": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": f"Erreur serveur: {str(e)}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeListByEntrepriseView(APIView):
    permission_classes = [IsAuthenticatedEntreprise]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé'],
        operation_description="Lister les employés de l'entreprise connectée.",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False,
                              description="Recherche (nom/email)"),
        ],
        responses={
            200: openapi.Response(description="Liste employés", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "donnees": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )),
            401: openapi.Response(description="Non authentifié", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            500: openapi.Response(description="Erreur serveur", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
        }
    )
    def get(self, request):
        try:
            q = request.GET.get('q')
            qs = Employe.objects.filter(entreprise=request.entreprise).select_related('prefix_telephone').order_by('-date_creation')
            if q:
                qs = qs.filter(email__icontains=q) | qs.filter(nom_complet__icontains=q)

            serializer = EmployeListSerializer(qs, many=True, context={'request': request})
            return Response({
                "message": "Liste des employés récupérée avec succès.",
                "success": True,
                "donnees": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeGetOneByEntrepriseView(APIView):
    permission_classes = [IsAuthenticatedEntreprise]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé'],
        operation_description="Récupérer un employé de l'entreprise par ID.",
        responses={
            200: openapi.Response(description="Employé", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            404: openapi.Response(description="Introuvable", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            500: openapi.Response(description="Erreur serveur", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
        }
    )
    def get(self, request, employe_id: int):
        try:
            employe = Employe.objects.filter(id=employe_id, entreprise=request.entreprise).first()
            if not employe:
                return Response({
                    "message": "Employé introuvable.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = EmployeListSerializer(employe, context={'request': request})
            return Response({
                "message": "Employé récupéré avec succès.",
                "success": True,
                "donnees": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeDeleteByEntrepriseView(APIView):
    permission_classes = [IsAuthenticatedEntreprise]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé'],
        operation_description="Supprimer un employé de l'entreprise.",
        responses={
            200: openapi.Response(description="Supprimé", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            404: openapi.Response(description="Introuvable", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            500: openapi.Response(description="Erreur serveur", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
        }
    )
    def delete(self, request, employe_id: int):
        try:
            employe = Employe.objects.filter(id=employe_id, entreprise=request.entreprise).first()
            if not employe:
                return Response({
                    "message": "Employé introuvable.",
                    "success": False,
                    "donnees": {}
                }, status=status.HTTP_404_NOT_FOUND)

            employe.delete()
            return Response({
                "message": "Employé supprimé avec succès.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeProfileView(APIView):
    permission_classes = [IsAuthenticatedEmploye]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Employé'],
        operation_description="Récupérer le profil de l'employé connecté.",
        responses={
            200: openapi.Response(description="Profil employé", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            401: openapi.Response(description="Non authentifié", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
        }
    )
    def get(self, request):
        try:
            # On réutilise le serializer list (tu peux faire un serializer "detail" si tu veux)
            serializer = EmployeListSerializer(request.employe, context={'request': request})
            return Response({
                "message": "Profil récupéré avec succès.",
                "success": True,
                "donnees": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeProfileUpdateView(APIView):
    permission_classes = [IsAuthenticatedEmploye]
    authentication_classes = []
    parser_classes = [FormParser, MultiPartParser]

    @swagger_auto_schema(
        tags=['Employé'],
        operation_description="Mettre à jour le profil de l'employé connecté (multipart/form-data).",
        manual_parameters=[
            openapi.Parameter('nom_complet', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('date_naissance', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              description="Format: YYYY-MM-DD"),
            openapi.Parameter('numero_telephone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('adresse', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('etat_civil', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              description="celibataire | marie | divorce | veuf"),
            openapi.Parameter('fonction', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('profession', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False,
                              description="ID profession (si tu autorises l'employé à changer)"),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
        ],
        responses={
            200: openapi.Response(description="Profil mis à jour", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            400: openapi.Response(description="Données invalides", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
            500: openapi.Response(description="Erreur serveur", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING),
                            "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "donnees": openapi.Schema(type=openapi.TYPE_OBJECT)}
            )),
        }
    )
    def patch(self, request):
        try:
            serializer = EmployeProfileUpdateSerializer(
                request.employe,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                serializer.save()
                out = EmployeListSerializer(request.employe, context={'request': request}).data
                return Response({
                    "message": "Profil mis à jour avec succès.",
                    "success": True,
                    "donnees": out
                }, status=status.HTTP_200_OK)

            return Response({
                "message": "Données invalides.",
                "success": False,
                "donnees": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": f"{str(e)}: {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

