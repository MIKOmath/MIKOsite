import random

from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.conf import settings
import requests
from mainSite.models import *
from accounts.models import *
from django.contrib.auth import login
from accounts.models import *
import os

from mikosite.secrets import CLIENT_ID, CLIENT_SECRET
REDIRECT_URI = '/discordauth/callback'
DISCORD_API_BASE_URL = 'https://discord.com/api'
SCOPE = 'identify email'

def home(request):
    user = request.session.get('user', None)
    return render(request, 'discordauth/home.html', {'user': user})

def login_view(request):
    # Generowanie URL do autoryzacji
    auth_url = f"{DISCORD_API_BASE_URL}/oauth2/authorize"
    redirect_url = "http://"+request.get_host() + REDIRECT_URI
    print(redirect_url)
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_url,
        "response_type": "code",
        "scope": SCOPE,
    }
    print(f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
    return redirect(f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")

def callback(request):
    # Pobieranie kodu autoryzacji z żądania
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'Brak kodu autoryzacji'}, status=400)
    redirect_url = "http://" + request.get_host() + REDIRECT_URI
    # Wymiana kodu na token dostępu
    token_url = f"{DISCORD_API_BASE_URL}/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri":  redirect_url,
        "scope": SCOPE,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        return JsonResponse({'error': 'Błąd wymiany kodu'}, status=400)

    token_data = response.json()
    access_token = token_data.get("access_token")

    # Pobieranie danych użytkownika
    user_url = f"{DISCORD_API_BASE_URL}/users/@me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_response = requests.get(user_url, headers=headers)
    if user_response.status_code != 200:
        return JsonResponse({'error': 'Błąd pobierania danych użytkownika'}, status=400)
    else:
        user_data = user_response.json()
        user, created = User.objects.get_or_create(username=user_data['username'],email=user_data['email'])
        login(request, user)
        external, created = LinkedAccount.objects.get_or_create(user=user,external_id=user_data['id'],platform='discord')
    return redirect('/discordauth/profile')

def logout(request):
    # Usuwanie danych użytkownika z sesji
    request.session.pop('user', None)
    return redirect('/discordauth/')
def user_profile(request):
    # Retrieve user data from the session
    user_data = request.user
    # Render the user profile template with the user data
    return render(request, 'discordauth/user_profile.html', {'user': user_data})