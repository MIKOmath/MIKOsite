from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("signout/", views.signout, name="signout"),
    # The auth pages moved under /accounts/; old bookmarks follow.
    path("signin/", RedirectView.as_view(pattern_name='account_login', permanent=True,
                                         query_string=True), name="signin"),
    path("signup/", RedirectView.as_view(pattern_name='account_signup', permanent=True,
                                         query_string=True), name="signup"),
    path("change_password/", RedirectView.as_view(pattern_name='account_change_password',
                                                  permanent=True), name="change_password"),
]
