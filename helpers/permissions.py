from rest_framework.permissions import BasePermission
from helpers.helper import get_token_from_request, get_entreprise, get_employe
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone as django_timezone
from apps.employe.models import EmployeCompte

class IsAuthenticatedEntrepriseOrEmploye(BasePermission):
    def has_permission(self, request, view):
        token = get_token_from_request(request)
        if not token:
            return False

        entreprise = get_entreprise(token)
        if entreprise is not None and not isinstance(entreprise, AnonymousUser):
        
            if not entreprise.est_actif or not entreprise.est_verifie:
                return False
        
            request.entreprise = entreprise
            return True
        employe = get_employe(token)
        if employe is None or isinstance(employe, AnonymousUser):
            return False

        try:
            compte = EmployeCompte.objects.get(employe=employe, est_actif=True)
            if compte.nombre_tentatives >= 5 and compte.bloque_jusqua and compte.bloque_jusqua > django_timezone.now():
                return False
        except EmployeCompte.DoesNotExist:
            return False

        if not employe.est_actif or not employe.entreprise.est_verifie:
            return False

        request.employe = employe
        return True
