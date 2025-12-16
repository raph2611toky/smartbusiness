from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
import uuid
from datetime import datetime, timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone as django_timezone
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from apps.entreprise.models import EntrepriseOutstandingToken
from helpers.helper import enc_dec

import traceback

class EntrepriseRefreshToken(RefreshToken):
    @classmethod
    def for_entreprise(cls, entreprise):
        try:
            if entreprise is None:
                raise TokenError("Entreprise not provided")

            token = cls()
            token['entreprise_id'] = entreprise.id
            token[enc_dec('type')] = enc_dec('entreprise')
            token['jti'] = str(uuid.uuid4())
            token.set_exp()
            
            if api_settings.BLACKLIST_AFTER_ROTATION:
                expires_at = datetime.fromtimestamp(token['exp'], tz=timezone.utc)
                EntrepriseOutstandingToken.objects.create(
                    entreprise=entreprise,
                    jti=token['jti'],
                    token=str(token),
                    expires_at=expires_at
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
            outstanding_token = EntrepriseOutstandingToken.objects.get(jti=self['jti'])
            outstanding_token.blacklisted = True
            outstanding_token.save()
        except EntrepriseOutstandingToken.DoesNotExist:
            raise TokenError('Token not found for blacklisting.')


class EntrepriseAccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.id) + six.text_type(timestamp) + six.text_type(user.is_email_verified)

account_activation_token = EntrepriseAccountActivationTokenGenerator()
