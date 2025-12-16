# apps/employe/urls.py
from django.urls import path
from apps.employe import auth as auth_views
from apps.employe import views as employe_views

app_name = "employe"

urlpatterns = [
    # AUTH
    path("auth/login/", auth_views.EmployeLoginView.as_view(), name="login"),
    path("auth/logout/", auth_views.EmployeLogoutView.as_view(), name="logout"),
    path("auth/forgot-password/", auth_views.EmployeForgotPasswordView.as_view(), name="forgot_password"),
    path("auth/reset-password/", auth_views.EmployeResetPasswordView.as_view(), name="reset_password"),
    path("auth/confirm-otp/", auth_views.EmployeConfirmOtpView.as_view(), name="confirm_otp"),
    path("auth/set-password/", auth_views.EmployeSetPasswordView.as_view(), name="set_password"),

    # CREATION (par entreprise)
    path("entreprise/create/", auth_views.EmployeCreateByEntrepriseView.as_view(), name="create_by_entreprise"),

    # VIEWS
    path("professions/", employe_views.ProfessionListView.as_view(), name="profession_list"),
    path("", employe_views.EmployeListByEntrepriseView.as_view(), name="employe_list_by_entreprise"),
    path("<int:employe_id>/", employe_views.EmployeGetOneByEntrepriseView.as_view(), name="employe_get_one_by_entreprise"),
    path("<int:employe_id>/delete/", employe_views.EmployeDeleteByEntrepriseView.as_view(), name="employe_delete_by_entreprise"),
    path("profile/", employe_views.EmployeProfileView.as_view(), name="profile"),
    path("profile/update/", employe_views.EmployeProfileUpdateView.as_view(), name="profile_update"),
]
