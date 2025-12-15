from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from datetime import timedelta
import random
import string
from dotenv import load_dotenv
import os

from apps.users.models import User, SmsOrangeToken, UserOtp
from helpers.services.emails import envoyer_email

load_dotenv()

class UserAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'email', 'is_active', 'is_staff', 'profile_url', 'actions_column')
    list_filter = ('is_active', 'is_staff', 'is_verified', 'is_superuser')
    search_fields = ('nom_complet', 'email', 'numero_phone')
    ordering = ('nom_complet',)

    def profile_url(self, obj):
        if obj.profile and obj.profile.url:
            p_url = f'{settings.BASE_URL}{settings.MEDIA_URL}{obj.profile}'
            return mark_safe(f'<a href="{p_url}" target="_blank"><img src="{p_url}" width="50" height="50" style="border-radius: 50%; object-fit: cover;"></a>')
        return 'Aucune image'
    profile_url.short_description = 'Photo de profil'

    def actions_column(self, obj):
        edit_url = reverse('admin:users_user_change', args=[obj.pk])
        delete_url = reverse('admin:users_user_delete', args=[obj.pk])
        toggle_url = reverse('admin:users_user_toggle_active', args=[obj.pk])

        return format_html(
            '<a href="{}" class="button edit-button" title="Modifier"><i class="fas fa-edit"></i></a> '
            '<a href="{}" class="button delete-button" title="Supprimer"><i class="fas fa-trash-alt"></i></a> '
            '<button class="button toggle-button {}" title="{}" onclick="toggleActive({})"><i class="fas {}"></i></button>',
            edit_url,
            delete_url,
            'active' if obj.is_active else 'inactive',
            'Désactiver' if obj.is_active else 'Activer',
            obj.pk,
            'fa-check' if obj.is_active else 'fa-times'
        )
    actions_column.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/toggle_active/', self.admin_site.admin_view(self.toggle_active_view), name='users_user_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request, user_id):
        user = self.get_object(request, user_id)
        if user:
            user.is_active = not user.is_active
            user.save()
            messages.success(request, f"Utilisateur {user.nom_complet} {'activé' if user.is_active else 'désactivé'}.")
        else:
            messages.error(request, "Utilisateur non trouvé.")
        return HttpResponseRedirect(reverse('admin:users_user_changelist'))

class SmsOrangeTokenAdmin(admin.ModelAdmin):
    list_display = ('token_access_truncated', 'token_type', 'token_validity', 'updated_at')
    search_fields = ('token_access', 'token_type')
    ordering = ('-updated_at',)

    def token_access_truncated(self, obj):
        return obj.token_access[:20] + '...' if len(obj.token_access) > 20 else obj.token_access
    token_access_truncated.short_description = 'Token d’accès'

class UserOtpAdmin(admin.ModelAdmin):
    list_display = ('code_otp', 'user_link', 'date_creation', 'expirer_le', 'is_expired', 'actions_column')
    list_filter = ('date_creation', 'expirer_le')
    search_fields = ('code_otp', 'user__nom_complet', 'user__email')
    ordering = ('-date_creation',)

    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.nom_complet)
        return 'Aucun utilisateur'
    user_link.short_description = 'Utilisateur'

    def is_expired(self, obj):
        return obj.expirer_le < timezone.now()
    is_expired.short_description = 'Expiré'
    is_expired.boolean = True

    def actions_column(self, obj):
        resend_url = reverse('admin:users_userotp_resend_otp', args=[obj.pk])
        return format_html(
            '<button class="button resend-button" title="Renvoyer OTP" onclick="resendOtp({})"><i class="fas fa-redo"></i></button>',
            obj.pk
        )
    actions_column.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:otp_id>/resend_otp/', self.admin_site.admin_view(self.resend_otp_view), name='users_userotp_resend_otp'),
        ]
        return custom_urls + urls

    def resend_otp_view(self, request, otp_id):
        otp = self.get_object(request, otp_id)
        if not otp:
            messages.error(request, "OTP non trouvé.")
            return HttpResponseRedirect(reverse('admin:users_userotp_changelist'))

        if otp.expirer_le >= timezone.now():
            messages.warning(request, f"L'OTP pour {otp.user.nom_complet} est encore valide jusqu'à {otp.expirer_le}.")
            return HttpResponseRedirect(reverse('admin:users_userotp_changelist'))

        # Generate new OTP
        new_otp_code = ''.join(random.choices(string.digits, k=6))
        otp.code_otp = new_otp_code
        otp.expirer_le = timezone.now() + timedelta(minutes=30)
        otp.date_creation = timezone.now()
        otp.save()

        # Send email
        email_data = {
            'subject': 'Nouvel OTP pour vérification de compte',
            'nom_complet': otp.user.nom_complet,
            'code_otp': new_otp_code,
            'site_url': os.getenv('SITE_URL'),
            'current_year': timezone.now().year
        }
        try:
            envoyer_email([otp.user.email], 'verify_email', email_data)
            messages.success(request, f"Nouvel OTP envoyé à {otp.user.nom_complet}.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi de l'OTP à {otp.user.nom_complet}: {str(e)}")
        return HttpResponseRedirect(reverse('admin:users_userotp_changelist'))

admin.site.register(User, UserAdmin)
admin.site.register(SmsOrangeToken, SmsOrangeTokenAdmin)
admin.site.register(UserOtp, UserOtpAdmin)