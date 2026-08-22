from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount


class AccountAdapter(DefaultAccountAdapter):
    def clean_username(self, username, shallow=False):
        # The DB constraint would turn an overlong username into a 500.
        username = super().clean_username(username, shallow=shallow)
        if len(username) > settings.MAX_USERNAME_LENGTH:
            raise ValidationError(
                f"Nazwa użytkownika jest za długa. Dopuszczalna liczba znaków: {settings.MAX_USERNAME_LENGTH}."
            )
        return username

    def save_user(self, request, user, form, commit=True):
        # The extras must land before the first save: date_of_birth is NOT NULL,
        # and allauth's own custom-signup hook runs only after the insert.
        user = super().save_user(request, user, form, commit=False)
        data = form.cleaned_data
        if data.get('region'):
            user.region = data['region']
        if data.get('date_of_birth'):
            user.date_of_birth = data['date_of_birth']
        if commit:
            user.save()
        return user

    def get_password_change_redirect_url(self, request):
        return reverse('profile')

    def add_message(self, *args, **kwargs):
        """Silenced: outcomes are shown inline, and nothing on the site renders
        the message store - undelivered messages would leak into the admin."""


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        # Discord has no real-name fields; allauth would pour the Discord
        # username into first_name.
        user = super().populate_user(request, sociallogin, data)
        if sociallogin.account.provider == 'discord':
            user.first_name = ''
            user.last_name = ''
        return user

    def pre_social_login(self, request, sociallogin):
        """One linked account per provider per member."""
        if sociallogin.is_existing:
            return
        if sociallogin.state.get('process') != 'connect':
            return
        if not request.user.is_authenticated:
            return
        provider = sociallogin.account.provider
        if SocialAccount.objects.filter(user=request.user, provider=provider).exists():
            url = reverse('socialaccount_connections') + '?blad=juz-polaczone'
            raise ImmediateHttpResponse(HttpResponseRedirect(url))
