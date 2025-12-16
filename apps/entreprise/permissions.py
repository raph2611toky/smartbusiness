from rest_framework.permissions import BasePermission
from helpers.helper import get_token_from_request, get_entreprise
from django.contrib.auth.models import AnonymousUser

class IsAuthenticatedEntreprise(BasePermission):
    def has_permission(self, request, view):
        token = get_token_from_request(request)
        if not token:
            return False

        entreprise = get_entreprise(token)
        if entreprise is None or isinstance(entreprise, AnonymousUser):
            return False
        
        if not entreprise.est_actif or not entreprise.est_verifie:
            return False
        
        request.entreprise = entreprise
        return True
