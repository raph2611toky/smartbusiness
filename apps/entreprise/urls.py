# apps/entreprise/urls.py
from django.urls import path
from apps.entreprise import auth, views

app_name = 'entreprise'

urlpatterns = [
    # Authentification & Inscription
    path('login/', auth.EntrepriseLoginView.as_view(), name='login'),
    path('register/', auth.EntrepriseRegisterView.as_view(), name='register'),
    path('google/callback/', auth.GoogleCallbackEntrepriseView.as_view(), name='google_callback'),
    
    # OTP Management
    path('verify-otp/', auth.VerifyEntrepriseOtpView.as_view(), name='verify_otp'),
    path('resend-otp/', auth.ResendEntrepriseOtpView.as_view(), name='resend_otp'),
    
    # Mot de passe
    path('mot-de-passe-oublie/', auth.EntrepriseMotDePasseOublieView.as_view(), name='mot_de_passe_oublie'),
    path('reset-password/', auth.EntrepriseResetPasswordView.as_view(), name='reset_password'),
    
    path('devises/liste/', views.DeviseListView.as_view(), name='devises_list'),
    path('prefix-telephones/liste/', views.PrefixTelephoneListView.as_view(), name='prefix_telephones_list'),

    # 👥 Entreprises (Authentifié)
    path('liste/', views.EntrepriseListView.as_view(), name='entreprises_list'),
    
    # 🏢 Profil Entreprise (Authentifié)
    path('profile/', views.EntrepriseProfileView.as_view(), name='profile'),
    path('profile/update/', views.EntrepriseProfileUpdateView.as_view(), name='profile_update'),
    
]
