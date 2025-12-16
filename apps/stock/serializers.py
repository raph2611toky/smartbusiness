from rest_framework import serializers
from django.utils import timezone
from apps.stock.models import Stock, UNITE_CHOICES
from apps.entreprise.models import Entreprise
from apps.employe.models import Employe

class StockListSerializer(serializers.ModelSerializer):
    cree_par_data = serializers.SerializerMethodField()
    est_en_rupture = serializers.SerializerMethodField()
    
    class Meta:
        model = Stock
        fields = [
            'id', 'nom', 'quantite', 'stock_min', 'unite', 'fournisseur',
            'cree_par_data', 'est_en_rupture', 'date_creation', 'date_modification', 'description'
        ]
    
    def get_cree_par_data(self, obj):
        if obj.cree_par:
            return {
                'id': obj.cree_par.id,
                'nom_complet': obj.cree_par.nom_complet
            }
        return None
    
    def get_est_en_rupture(self, obj):
        return obj.est_en_rupture

class StockCreateSerializer(serializers.ModelSerializer):
    cree_par = serializers.PrimaryKeyRelatedField(
        queryset=Employe.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    
    class Meta:
        model = Stock
        fields = ['nom', 'quantite', 'stock_min', 'unite', 'fournisseur', 'cree_par', 'description']
    
    def validate(self, attrs):
        entreprise = self.context.get('entreprise')
        if not entreprise:
            raise serializers.ValidationError("Entreprise requise.")
        
        nom = attrs.get('nom', '').strip()
        if Stock.objects.filter(nom__iexact=nom, entreprise=entreprise).exists():
            raise serializers.ValidationError("Stock avec ce nom existe déjà.")
        
        if attrs.get('quantite', 0) < 0:
            raise serializers.ValidationError("Quantité ne peut pas être négative.")
        if attrs.get('stock_min', 0) < 0:
            raise serializers.ValidationError("Stock minimum ne peut pas être négatif.")
        
        unite = attrs.get('unite', 'kg')
        if unite not in dict(UNITE_CHOICES):
            raise serializers.ValidationError("Unité invalide.")
            
        return attrs
    
    def create(self, validated_data):
        entreprise = self.context['entreprise']
        validated_data['entreprise'] = entreprise
        return super().create(validated_data)

class StockUpdateSerializer(serializers.ModelSerializer):
    quantite_delta = serializers.DecimalField(
        max_digits=12, decimal_places=2, 
        required=False,
        help_text="Incrément/décrément de quantité (ex: 50 pour +50kg, -25 pour -25kg)"
    )
    
    class Meta:
        model = Stock
        fields = ['quantite', 'stock_min', 'unite', 'fournisseur', 'quantite_delta']
    
    def update(self, instance, validated_data):
        quantite_delta = validated_data.pop('quantite_delta', None)
        
        if quantite_delta is not None:
            nouvelle_quantite = instance.quantite + quantite_delta
            if nouvelle_quantite < 0:
                raise serializers.ValidationError("Quantité ne peut pas devenir négative.")
            instance.quantite = nouvelle_quantite
            validated_data['quantite'] = instance.quantite
        
        return super().update(instance, validated_data)
