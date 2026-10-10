from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="profile_index"),
    path("register/", views.register, name="profile_register"),
    path("login/", views.login_view, name="profile_login"),
    path("logout/", views.logout_view, name="profile_logout"),
    path("me/", views.profile, name="profile_detail"),
    path("verify-email/<str:token>/", views.verify_email, name="profile_verify_email"),
    path("email-verification-sent/", views.verify_email_sent, name="profile_verify_email_sent"),
    path("password-reset/", views.password_reset_request, name="profile_password_reset"),
    path("password-reset/<str:token>/", views.password_reset_confirm, name="profile_password_reset_confirm"),
]
