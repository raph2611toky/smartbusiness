# apps/entreprise/permissions.py - Ajoutez cette classe
from rest_framework.permissions import BasePermission
from helpers.helper import get_token_from_request, get_employe
from django.utils import timezone as django_timezone
from django.contrib.auth.models import AnonymousUser
from apps.employe.models import EmployeCompte

class IsAuthenticatedEmploye(BasePermission):
    def has_permission(self, request, view):
        token = get_token_from_request(request)
        if not token:
            return False

        employe = get_employe(token)
        if employe is None or isinstance(employe, AnonymousUser):
            return False

        try:
            compte = EmployeCompte.objects.get(employe=employe, est_actif=True)
            if compte.nombre_tentatives >= 5 and compte.bloque_jusqua and compte.bloque_jusqua > django_timezone.now():
                return False
        except EmployeCompte.DoesNotExist:
            return False

        if not employe.est_actif or not employe.entreprise.est_actif:
            return False

        request.employe = employe
        return True

class IsEmployeEntreprise(BasePermission):
    """Employé appartient à l'entreprise connectée"""
    def has_permission(self, request, view):
        if not hasattr(request, 'entreprise') or not request.entreprise:
            return False
        return request.employe and request.employe.entreprise == request.entreprise
