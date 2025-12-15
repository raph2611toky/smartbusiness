from django.urls import path
from apps.users.views import (
    ProfileView, LogoutView, ProfileUpdateView, UserVerifyOtpView, UserMotDePasseOublieView,
    UserResetPasswordView, ContactSupportView, ResendOTPVerificationView,
)
from apps.users.auth import (
    RegisterView, LoginView, GoogleCallbackUserView, GoogleAuthUrlView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),  # POST
    path('register/', RegisterView.as_view(), name="register-client"),  # POST
    path('auth/google/redirect/', GoogleAuthUrlView.as_view(), name="google-redirection"),  # GET
    path('auth/google/callback/', GoogleCallbackUserView.as_view(), name="google-callback"),  # POST
    path('profile/', ProfileView.as_view(), name="profile"),  # GET
    path('profile/update/', ProfileUpdateView.as_view(), name="profile-update"),  # PUT
    path('logout/', LogoutView.as_view(), name='logout'),  # PUT
    path('user/verify-otp/', UserVerifyOtpView.as_view(), name='user-verification-otp'),  # POST
    path('user/resend-otp/', ResendOTPVerificationView.as_view(), name='user-resend-otp'),  # POST
    path('user/mot-de-passe/oublier/', UserMotDePasseOublieView.as_view(), name='user-mot-de-passe-oublier'),  # POST
    path('user/mot-de-passe/reset/', UserResetPasswordView.as_view(), name='user-reset-password'),  # POST
    path('contact-support/', ContactSupportView.as_view(), name='contact-support'),  # POST
]