from rest_framework.permissions import BasePermission
from helpers.helper import get_token_from_request, get_user
from django.contrib.auth.models import AnonymousUser

class IsNotSuperuser(BasePermission):
    def has_permission(self, request, view):
        token = get_token_from_request(request)
        if not token:
            return False

        user = get_user(token)
        if user is None or isinstance(user, AnonymousUser):
            return False
        
        if not user.is_active or user.is_superuser:
            return False
        
        request.user = user
        return True
