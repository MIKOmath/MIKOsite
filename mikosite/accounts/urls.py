from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("signout/", views.signout, name="signout"),
    path("profile/", views.profile, name="profile"),
    path("publicprofile/<str:username>/", views.public_profile, name="publicprofile"),
    path("change_password/", views.change_password, name="change_password"),
]
