from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback
from .models import Facture
from .serializers import (
    FactureListSerializer, FactureCreateSerializer, FactureUpdateSerializer
)
from helpers.permissions import IsAuthenticatedEntrepriseOrEmploye

# Schemas JSON 100% manuels (PAS de serializer dans Swagger)
RESPONSE_JSON = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
    }
)

RESPONSE_JSON_LIST = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'donnees': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'numero': openapi.Schema(type=openapi.TYPE_STRING),
                    'client': openapi.Schema(type=openapi.TYPE_STRING),
                    'montant': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'statut': openapi.Schema(type=openapi.TYPE_STRING),
                    'date_facture': openapi.Schema(type=openapi.TYPE_STRING),
                    'date_echeance': openapi.Schema(type=openapi.TYPE_STRING),
                    'est_payee': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'est_echue': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        )
    }
)

RESPONSE_JSON_DETAIL = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'donnees': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'numero': openapi.Schema(type=openapi.TYPE_STRING),
                'client': openapi.Schema(type=openapi.TYPE_STRING),
                'montant': openapi.Schema(type=openapi.TYPE_NUMBER),
                'prefix_telephone_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                'statut': openapi.Schema(type=openapi.TYPE_STRING),
                'date_facture': openapi.Schema(type=openapi.TYPE_STRING),
                'date_echeance': openapi.Schema(type=openapi.TYPE_STRING),
                'est_payee': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'est_echue': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        )
    }
)

class FactureListView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    @swagger_auto_schema(
        tags=['Facture'],
        manual_parameters=[
            openapi.Parameter('statut', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description="Recherche numero/client")
        ],
        responses={
            200: openapi.Response('Liste factures', RESPONSE_JSON_LIST),
            401: openapi.Response('Non authentifié', RESPONSE_JSON),
            403: openapi.Response('Non autorisé', RESPONSE_JSON),
            500: openapi.Response('Erreur serveur', RESPONSE_JSON)
        },
        operation_description="Lister toutes les factures de l'entreprise connectée."
    )
    def get(self, request):
        try:
            filters = {}
            statut = request.GET.get('statut')
            q = request.GET.get('q', '')
            
            entreprise = getattr(request, 'entreprise', request.employe.entreprise)
            qs = Facture.objects.filter(entreprise=entreprise)
            
            if statut:
                qs = qs.filter(statut=statut)
            if q:
                qs = qs.filter(
                    numero__icontains=q
                ) | qs.filter(
                    client__icontains=q
                )
            
            qs = qs.select_related('prefix_telephone', 'cree_par').order_by('-date_creation')
            serializer = FactureListSerializer(qs, many=True)
            return Response({
                "message": "Factures récupérées avec succès.",
                "success": True,
                "donnees": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": f"Erreur serveur: {str(e)}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FactureCreateView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    @swagger_auto_schema(
        tags=['Facture'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['client', 'montant', 'date_facture', 'date_echeance'],
            properties={
                'numero': openapi.Schema(type=openapi.TYPE_STRING, example="FAC-2025-001"),
                'client': openapi.Schema(type=openapi.TYPE_STRING, example="Client ABC"),
                'montant': openapi.Schema(type=openapi.TYPE_NUMBER, example="15000.00"),
                'prefix_telephone': openapi.Schema(type=openapi.TYPE_INTEGER, example=125),
                'date_facture': openapi.Schema(type=openapi.TYPE_STRING, example="2025-12-16"),
                'date_echeance': openapi.Schema(type=openapi.TYPE_STRING, example="2026-01-16"),
                'statut': openapi.Schema(type=openapi.TYPE_STRING, example="brouillon"),
                'motif': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'cree_par': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            201: openapi.Response('Facture créée', RESPONSE_JSON_DETAIL),
            400: openapi.Response('Données invalides', RESPONSE_JSON),
            500: openapi.Response('Erreur serveur', RESPONSE_JSON)
        }
    )
    def post(self, request):
        try:
            entreprise = getattr(request, 'entreprise', request.employe.entreprise)
            serializer = FactureCreateSerializer(
                data=request.data,
                context={'entreprise': entreprise}
            )
            
            if serializer.is_valid():
                facture = serializer.save()
                return Response({
                    "message": "Facture créée avec succès.",
                    "success": True,
                    "donnees": FactureListSerializer(facture).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "message": "Données invalides.",
                "success": False,
                "donnees": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "message": f"Erreur serveur: {str(e)} - {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FactureDetailView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    def get_object(self, facture_id):
        entreprise = getattr(self.request, 'entreprise', self.request.employe.entreprise)
        try:
            return Facture.objects.get(id=facture_id, entreprise=entreprise)
        except Facture.DoesNotExist:
            raise Exception("Facture introuvable.")
    
    @swagger_auto_schema(
        tags=['Facture'],
        responses={
            200: openapi.Response('Détail facture', RESPONSE_JSON_DETAIL),
            404: openapi.Response('Facture introuvable', RESPONSE_JSON)
        }
    )
    def get(self, request, facture_id):
        try:
            facture = self.get_object(facture_id)
            return Response({
                "message": "Facture récupérée avec succès.",
                "success": True,
                "donnees": FactureListSerializer(facture).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e),
                "success": False,
                "donnees": {}
            }, status=status.HTTP_404_NOT_FOUND)

class FactureUpdateView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    def get_object(self, facture_id):
        entreprise = getattr(self.request, 'entreprise', self.request.employe.entreprise)
        try:
            return Facture.objects.get(id=facture_id, entreprise=entreprise)
        except Facture.DoesNotExist:
            raise Exception("Facture introuvable.")
    
    @swagger_auto_schema(
        tags=['Facture'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'client': openapi.Schema(type=openapi.TYPE_STRING, example="Client ABC"),
                'montant': openapi.Schema(type=openapi.TYPE_NUMBER, example="16000.00"),
                'prefix_telephone': openapi.Schema(type=openapi.TYPE_INTEGER, example=125),
                'date_echeance': openapi.Schema(type=openapi.TYPE_STRING, example="2026-01-30"),
                'statut': openapi.Schema(type=openapi.TYPE_STRING, example="payee"),
                'motif': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            200: openapi.Response('Facture mise à jour', RESPONSE_JSON_DETAIL),
            400: openapi.Response('Données invalides', RESPONSE_JSON),
            404: openapi.Response('Facture introuvable', RESPONSE_JSON)
        }
    )
    def patch(self, request, facture_id):
        try:
            facture = self.get_object(facture_id)
            serializer = FactureUpdateSerializer(facture, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Facture mise à jour avec succès.",
                    "success": True,
                    "donnees": FactureListSerializer(facture).data
                }, status=status.HTTP_200_OK)
            
            return Response({
                "message": "Données invalides.",
                "success": False,
                "donnees": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "message": f"{str(e)} - {str(traceback.format_exc())}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_400_BAD_REQUEST)

class FactureDeleteView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    def get_object(self, facture_id):
        entreprise = getattr(self.request, 'entreprise', self.request.employe.entreprise)
        try:
            return Facture.objects.get(id=facture_id, entreprise=entreprise)
        except Facture.DoesNotExist:
            raise Exception("Facture introuvable.")
    
    @swagger_auto_schema(
        tags=['Facture'],
        responses={
            200: openapi.Response('Facture supprimée', RESPONSE_JSON),
            404: openapi.Response('Facture introuvable', RESPONSE_JSON)
        }
    )
    def delete(self, request, facture_id):
        try:
            facture = self.get_object(facture_id)
            numero = facture.numero
            facture.delete()
            return Response({
                "message": f"Facture '{numero}' supprimée avec succès.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e),
                "success": False,
                "donnees": {}
            }, status=status.HTTP_404_NOT_FOUND)
