from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import traceback
from .models import Stock
from .serializers import (
    StockListSerializer, StockCreateSerializer, StockUpdateSerializer
)
from helpers.permissions import IsAuthenticatedEntrepriseOrEmploye

# Schema JSON standard UNIQUEMENT avec objets simples
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
                    'nom': openapi.Schema(type=openapi.TYPE_STRING),
                    'quantite': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'stock_min': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'unite': openapi.Schema(type=openapi.TYPE_STRING),
                    'fournisseur': openapi.Schema(type=openapi.TYPE_STRING),
                    'cree_par_data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    'est_en_rupture': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'date_creation': openapi.Schema(type=openapi.TYPE_STRING),
                    'date_modification': openapi.Schema(type=openapi.TYPE_STRING)
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
                'nom': openapi.Schema(type=openapi.TYPE_STRING),
                'quantite': openapi.Schema(type=openapi.TYPE_NUMBER),
                'stock_min': openapi.Schema(type=openapi.TYPE_NUMBER),
                'unite': openapi.Schema(type=openapi.TYPE_STRING),
                'fournisseur': openapi.Schema(type=openapi.TYPE_STRING),
                'cree_par_data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                'est_en_rupture': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'date_creation': openapi.Schema(type=openapi.TYPE_STRING),
                'date_modification': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    }
)

class StockListView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    @swagger_auto_schema(
        tags=['Stock'],
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description="Recherche par nom")
        ],
        responses={
            200: openapi.Response('Liste stocks', RESPONSE_JSON_LIST),
            401: openapi.Response('Non authentifié', RESPONSE_JSON),
            403: openapi.Response('Non autorisé', RESPONSE_JSON),
            500: openapi.Response('Erreur serveur', RESPONSE_JSON)
        },
        operation_description="Lister tous les stocks de l'entreprise connectée."
    )
    def get(self, request):
        try:
            q = request.GET.get('q', '')
            
            if hasattr(request, 'entreprise'):
                qs = Stock.objects.filter(entreprise=request.entreprise)
            else:  # employé
                qs = Stock.objects.filter(entreprise=request.employe.entreprise)
            
            if q:
                qs = qs.filter(nom__icontains=q)
            
            qs = qs.select_related('cree_par', 'entreprise').order_by('-date_creation')
            serializer = StockListSerializer(qs, many=True)
            return Response({
                "message": "Stocks récupérés avec succès.",
                "success": True,
                "donnees": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": f"Erreur serveur: {str(e)}",
                "success": False,
                "donnees": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StockCreateView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    @swagger_auto_schema(
        tags=['Stock'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['nom', 'quantite', 'stock_min', 'fournisseur'],
            properties={
                'nom': openapi.Schema(type=openapi.TYPE_STRING, example="Riz"),
                'quantite': openapi.Schema(type=openapi.TYPE_NUMBER, example="500.00"),
                'stock_min': openapi.Schema(type=openapi.TYPE_NUMBER, example="100.00"),
                'unite': openapi.Schema(type=openapi.TYPE_STRING, example="kg"),
                'fournisseur': openapi.Schema(type=openapi.TYPE_STRING, example="Fournisseur A"),
                'cree_par': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            201: openapi.Response('Stock créé', RESPONSE_JSON_DETAIL),
            400: openapi.Response('Données invalides', RESPONSE_JSON),
            500: openapi.Response('Erreur serveur', RESPONSE_JSON)
        },
        operation_description="Créer un nouveau stock."
    )
    def post(self, request):
        try:
            entreprise = getattr(request, 'entreprise', request.employe.entreprise)
            serializer = StockCreateSerializer(
                data=request.data, 
                context={'entreprise': entreprise}
            )
            
            if serializer.is_valid():
                stock = serializer.save()
                return Response({
                    "message": "Stock créé avec succès.",
                    "success": True,
                    "donnees": StockListSerializer(stock).data
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

class StockDetailView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    def get_object(self, stock_id):
        entreprise = getattr(self.request, 'entreprise', self.request.employe.entreprise)
        try:
            obj = Stock.objects.get(id=stock_id, entreprise=entreprise)
            return obj
        except Stock.DoesNotExist:
            raise Exception("Stock introuvable.")
    
    @swagger_auto_schema(
        tags=['Stock'],
        responses={
            200: openapi.Response('Détail stock', RESPONSE_JSON_DETAIL),
            404: openapi.Response('Stock introuvable', RESPONSE_JSON)
        },
        operation_description="Récupérer le détail d'un stock."
    )
    def get(self, request, stock_id):
        try:
            stock = self.get_object(stock_id)
            return Response({
                "message": "Stock récupéré avec succès.",
                "success": True,
                "donnees": StockListSerializer(stock).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e),
                "success": False,
                "donnees": {}
            }, status=status.HTTP_404_NOT_FOUND)

class StockUpdateView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    def get_object(self, stock_id):
        entreprise = getattr(self.request, 'entreprise', self.request.employe.entreprise)
        try:
            obj = Stock.objects.get(id=stock_id, entreprise=entreprise)
            return obj
        except Stock.DoesNotExist:
            raise Exception("Stock introuvable.")
    
    @swagger_auto_schema(
        tags=['Stock'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantite': openapi.Schema(type=openapi.TYPE_NUMBER, example="550.00"),
                'stock_min': openapi.Schema(type=openapi.TYPE_NUMBER, example="100.00"),
                'unite': openapi.Schema(type=openapi.TYPE_STRING, example="kg"),
                'fournisseur': openapi.Schema(type=openapi.TYPE_STRING, example="Fournisseur A"),
                'quantite_delta': openapi.Schema(type=openapi.TYPE_NUMBER, example="50.00", description="+/- quantité")
            }
        ),
        responses={
            200: openapi.Response('Stock mis à jour', RESPONSE_JSON_DETAIL),
            400: openapi.Response('Données invalides', RESPONSE_JSON),
            404: openapi.Response('Stock introuvable', RESPONSE_JSON)
        },
        operation_description="Mettre à jour un stock (+/- quantité avec quantite_delta)."
    )
    def patch(self, request, stock_id):
        try:
            stock = self.get_object(stock_id)
            serializer = StockUpdateSerializer(stock, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Stock mis à jour avec succès.",
                    "success": True,
                    "donnees": StockListSerializer(stock).data
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

class StockDeleteView(APIView):
    permission_classes = [IsAuthenticatedEntrepriseOrEmploye]
    
    def get_object(self, stock_id):
        entreprise = getattr(self.request, 'entreprise', self.request.employe.entreprise)
        try:
            obj = Stock.objects.get(id=stock_id, entreprise=entreprise)
            return obj
        except Stock.DoesNotExist:
            raise Exception("Stock introuvable.")
    
    @swagger_auto_schema(
        tags=['Stock'],
        responses={
            200: openapi.Response('Stock supprimé', RESPONSE_JSON),
            404: openapi.Response('Stock introuvable', RESPONSE_JSON)
        },
        operation_description="Supprimer un stock."
    )
    def delete(self, request, stock_id):
        try:
            stock = self.get_object(stock_id)
            nom = stock.nom
            stock.delete()
            return Response({
                "message": f"Stock '{nom}' supprimé avec succès.",
                "success": True,
                "donnees": {}
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e),
                "success": False,
                "donnees": {}
            }, status=status.HTTP_404_NOT_FOUND)
