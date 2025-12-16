from rest_framework import serializers
from django.utils import timezone
from .models import Facture, STATUT_CHOICES
from apps.entreprise.models import Entreprise, PrefixTelephone
from apps.employe.models import Employe

class PrefixTelephoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrefixTelephone
        fields = ['id', 'prefix', 'pays']

class FactureListSerializer(serializers.ModelSerializer):
    prefix_telephone_data = PrefixTelephoneSerializer(read_only=True)
    cree_par_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Facture
        fields = [
            'id', 'numero', 'client', 'montant', 'prefix_telephone_data',
            'date_facture', 'date_echeance', 'statut', 'motif', 'description',
            'cree_par_data', 'est_payee', 'est_echue', 'date_creation', 'date_modification'
        ]
    
    def get_cree_par_data(self, obj):
        if obj.cree_par:
            return {
                'id': obj.cree_par.id,
                'nom_complet': obj.cree_par.nom_complet
            }
        return None

class FactureCreateSerializer(serializers.ModelSerializer):
    prefix_telephone = serializers.PrimaryKeyRelatedField(
        queryset=PrefixTelephone.objects.all(),
        required=False,
        default=125
    )
    cree_par = serializers.PrimaryKeyRelatedField(
        queryset=Employe.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    
    class Meta:
        model = Facture
        fields = [
            'numero', 'client', 'montant', 'prefix_telephone',
            'date_facture', 'date_echeance', 'statut', 'motif', 'description', 'cree_par'
        ]
    
    def validate(self, attrs):
        entreprise = self.context.get('entreprise')
        if not entreprise:
            raise serializers.ValidationError("Entreprise requise.")
        
        numero = attrs.get('numero', '').strip()
        if Facture.objects.filter(numero=numero, entreprise=entreprise).exists():
            raise serializers.ValidationError("Numéro de facture dupliqué.")
        
        if attrs.get('montant', 0) <= 0:
            raise serializers.ValidationError("Montant doit être positif.")
        
        date_facture = attrs.get('date_facture')
        date_echeance = attrs.get('date_echeance')
        if date_facture and date_echeance and date_echeance < date_facture:
            raise serializers.ValidationError("Date d'échéance ne peut pas être antérieure à la date de facture.")
        
        return attrs
    
    def create(self, validated_data):
        entreprise = self.context['entreprise']
        validated_data['entreprise'] = entreprise
        
        # Générer numero auto si vide
        numero = validated_data.get('numero')
        if not numero:
            validated_data['numero'] = f"FAC-{timezone.now().year}-{entreprise.id:04d}"
        
        return super().create(validated_data)

class FactureUpdateSerializer(serializers.ModelSerializer):
    prefix_telephone = serializers.PrimaryKeyRelatedField(
        queryset=PrefixTelephone.objects.all(),
        required=False
    )
    
    class Meta:
        model = Facture
        fields = [
            'montant', 'prefix_telephone', 'date_echeance', 'statut', 
            'motif', 'description', 'client'
        ]
    
    def validate(self, attrs):
        if 'statut' in attrs:
            statut = attrs['statut']
            if statut not in dict(STATUT_CHOICES):
                raise serializers.ValidationError("Statut invalide.")
        return attrs
