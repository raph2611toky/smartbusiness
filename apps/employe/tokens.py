from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
import uuid
from datetime import datetime, timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone as django_timezone
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from apps.employe.models import EmployeOutstandingToken
from helpers.helper import enc_dec

import traceback

class EmployeRefreshToken(RefreshToken):
    @classmethod
    def for_employe(cls, employe):
        try:
            if employe is None:
                raise TokenError("Employe not provided")

            token = cls()
            token['employe_id'] = employe.id
            token[enc_dec('type')] = enc_dec('employe')
            token['jti'] = str(uuid.uuid4())
            token.set_exp()
            
            if api_settings.BLACKLIST_AFTER_ROTATION:
                expires_at = datetime.fromtimestamp(token['exp'], tz=timezone.utc)
                EmployeOutstandingToken.objects.create(
                    employe=employe,
                    jti=token['jti'],
                    token=str(token),
                    date_expiration=expires_at
                )

            return token
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return None

    def set_exp(self, from_time=None, lifetime=None):
        if from_time is None:
            from_time = django_timezone.now()

        if lifetime is None:
            lifetime = api_settings.REFRESH_TOKEN_LIFETIME

        super().set_exp(from_time=from_time, lifetime=lifetime)

        self.access_token.set_exp(
            from_time=from_time,
            lifetime=api_settings.ACCESS_TOKEN_LIFETIME
        )
        
    def blacklist(self):
        try:
            outstanding_token = EmployeOutstandingToken.objects.get(jti=self['jti'])
            outstanding_token.blacklisted = True
            outstanding_token.save()
        except EmployeOutstandingToken.DoesNotExist:
            raise TokenError('Token not found for blacklisting.')


class EmployeAccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.id) + six.text_type(timestamp) + six.text_type(user.is_email_verified)

account_activation_token = EmployeAccountActivationTokenGenerator()
