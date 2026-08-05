from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="accounts_index"),
    path("register/", views.register, name="accounts_register"),
    path("login/", views.login_view, name="accounts_login"),
    path("logout/", views.logout_view, name="accounts_logout"),
    path("profile/", views.profile, name="accounts_profile"),
    path("verify-email/<str:token>/", views.verify_email, name="accounts_verify_email"),
    path("email-verification-sent/", views.verify_email_sent, name="accounts_verify_email_sent"),
    path("password-reset/", views.password_reset_request, name="accounts_password_reset"),
    path("password-reset/<str:token>/", views.password_reset_confirm, name="accounts_password_reset_confirm"),
]

