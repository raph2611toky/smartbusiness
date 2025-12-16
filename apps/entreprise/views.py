from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from dotenv import load_dotenv

from apps.entreprise.permissions import IsAuthenticatedEntreprise
from apps.entreprise.serializers import EntrepriseSerializer, DeviseSerializer, PrefixTelephoneSerializer
from apps.entreprise.models import Entreprise, Devise, PrefixTelephone

load_dotenv()

## 1. LISTE DEVISES (Public)
class DeviseListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Référence'],
        responses={
            200: openapi.Response(
                description="Liste des devises",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'nom_court': openapi.Schema(type=openapi.TYPE_STRING),
                                    'nom_long': openapi.Schema(type=openapi.TYPE_STRING),
                                    'pays': openapi.Schema(type=openapi.TYPE_STRING),
                                    'drapeau_image': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                                }
                            )
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
        operation_description="Récupérer la liste complète des devises disponibles."
    )
    def get(self, request):
        try:
            devises = Devise.objects.all().order_by('nom_court')
            serializer = DeviseSerializer(devises, many=True)
            return Response({
                'message': 'Liste des devises récupérée avec succès',
                'success': True,
                'donnees': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


## 2. LISTE PREFIX TELEPHONE (Public)  
class PrefixTelephoneListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=['Référence'],
        responses={
            200: openapi.Response(
                description="Liste des préfixes téléphoniques",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'prefix': openapi.Schema(type=openapi.TYPE_STRING),
                                    'pays': openapi.Schema(type=openapi.TYPE_STRING),
                                    'drapeau_image': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                                }
                            )
                        )
                    }
                )
            ),
            500: 'Erreur serveur'
        },
        operation_description="Récupérer la liste complète des préfixes téléphoniques."
    )
    def get(self, request):
        try:
            prefixes = PrefixTelephone.objects.all().order_by('prefix')
            serializer = PrefixTelephoneSerializer(prefixes, many=True)
            return Response({
                'message': 'Liste des préfixes téléphoniques récupérée',
                'success': True,
                'donnees': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


## 3. LISTE ENTREPRISES (Authentifié uniquement)
class EntrepriseListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Entreprise'],
        responses={
            200: openapi.Response(
                description="Liste des entreprises",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'nom_complet': openapi.Schema(type=openapi.TYPE_STRING),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                                    'type_entreprise': openapi.Schema(type=openapi.TYPE_STRING),
                                    'est_verifie': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'est_actif': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                                }
                            )
                        )
                    }
                )
            ),
            401: 'Non authentifié',
            403: 'Non autorisé',
            500: 'Erreur serveur'
        },
        operation_description="Récupérer la liste de toutes les entreprises (admin uniquement)."
    )
    def get(self, request):
        try:
            entreprises = Entreprise.objects.filter(
                est_actif=True
            ).select_related('plan', 'prefix_telephone').order_by('-date_creation')[:50]
            
            serializer = EntrepriseSerializer(entreprises, many=True)
            return Response({
                'message': 'Liste des entreprises récupérée',
                'success': True,
                'donnees': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


## 4. PROFIL ENTREPRISE (Authentifié)
class EntrepriseProfileView(APIView):
    permission_classes = [IsAuthenticatedEntreprise]
    parser_classes = [FormParser, MultiPartParser]

    @swagger_auto_schema(
        tags=['Entreprise'],
        responses={
            200: openapi.Response(
                description="Profil entreprise",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'nom_complet': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'type_entreprise': openapi.Schema(type=openapi.TYPE_STRING),
                                'profile_url': openapi.Schema(type=openapi.TYPE_STRING),
                                'nif_stat': openapi.Schema(type=openapi.TYPE_STRING),
                                'est_verifie': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'plan': openapi.Schema(type=openapi.TYPE_OBJECT)
                            }
                        )
                    }
                )
            ),
            401: 'Non authentifié',
            500: 'Erreur serveur'
        },
        operation_description="Récupérer le profil complet de l'entreprise connectée."
    )
    def get(self, request):
        try:
            entreprise = request.entreprise
            serializer = EntrepriseSerializer(entreprise)
            return Response({
                'message': 'Profil entreprise récupéré',
                'success': True,
                'donnees': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## 5. UPDATE PROFIL ENTREPRISE (Authentifié + Upload Image) - CORRIGÉE
class EntrepriseProfileUpdateView(APIView):
    permission_classes = [IsAuthenticatedEntreprise]
    parser_classes = [FormParser, MultiPartParser]
    http_method_names = ['put', 'patch']

    @swagger_auto_schema(
        tags=['Entreprise'],
        manual_parameters=[
            openapi.Parameter(
                'nom_complet', 
                openapi.IN_FORM,
                description="Nom complet de l'entreprise",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'description', 
                openapi.IN_FORM,
                description="Description de l'entreprise",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'type_entreprise', 
                openapi.IN_FORM,
                description="Type d'entreprise (SARL, SA, SAS, EURL, EI, AUTRE)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'nif_stat', 
                openapi.IN_FORM,
                description="NIF/Stat",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'numero_telephone', 
                openapi.IN_FORM,
                description="Numéro de téléphone (sans préfixe)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'prefix_telephone', 
                openapi.IN_FORM,
                description="ID du préfixe téléphonique",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'profile', 
                openapi.IN_FORM,
                description="Photo de profil (JPG, PNG, max 2MB)",
                type=openapi.TYPE_FILE,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Profil mis à jour",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                        'donnees': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'nom_complet': openapi.Schema(type=openapi.TYPE_STRING),
                                'profile_url': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                'message_update': openapi.Schema(type=openapi.TYPE_STRING),
                                'champs_modifies': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING)
                                )
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
            401: openapi.Response(
                description="Non authentifié",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                        'donnees': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            413: openapi.Response(
                description="Fichier trop volumineux",
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
        operation_description="Mettre à jour le profil de l'entreprise connectée (PUT/PATCH + upload photo multipart/form-data)."
    )
    def put(self, request):
        return self.update_profile(request)

    def update_profile(self, request):
        try:
            entreprise = request.entreprise
            champs_modifies = []

            # Validation taille fichier
            profile_file = request.FILES.get('profile')
            if profile_file:
                if profile_file.size > 2 * 1024 * 1024:  # 2MB
                    return Response({
                        'message': 'Fichier trop volumineux. Maximum 2MB autorisé.',
                        'success': False,
                        'donnees': {}
                    }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

            # Préparer les données pour le serializer
            data = request.data.copy()
            serializer = EntrepriseSerializer(
                entreprise,
                data=data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                # Détecter les champs modifiés
                if 'nom_complet' in data and data['nom_complet'] != entreprise.nom_complet:
                    champs_modifies.append('nom_complet')
                if 'description' in data and data['description'] != entreprise.description:
                    champs_modifies.append('description')
                if 'profile' in request.FILES:
                    champs_modifies.append('profile')
                if 'type_entreprise' in data and data['type_entreprise'] != entreprise.type_entreprise:
                    champs_modifies.append('type_entreprise')
                if 'numero_telephone' in data and data['numero_telephone'] != entreprise.numero_telephone:
                    champs_modifies.append('numero_telephone')

                serializer.save()
                
                return Response({
                    'message': f'Profil mis à jour avec succès ({len(champs_modifies)} champ(s) modifié(s))',
                    'success': True,
                    'donnees': {
                        'nom_complet': serializer.data.get('nom_complet'),
                        'profile_url': serializer.data.get('profile_url'),
                        'message_update': 'Changements appliqués avec succès',
                        'champs_modifies': champs_modifies if champs_modifies else ['Aucun changement détecté']
                    }
                }, status=status.HTTP_200_OK)

            return Response({
                'message': 'Données invalides lors de la mise à jour',
                'success': False,
                'donnees': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Update profile error: {str(e)}")
            return Response({
                'message': f"Erreur serveur: {str(e)}",
                'success': False,
                'donnees': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

