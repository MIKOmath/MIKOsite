import datetime

from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password, password_validators_help_texts
from django.core.exceptions import ValidationError

User = get_user_model()


def signup(request):
    ctx = {
        "region_choices": User._meta.get_field('region').choices,
        "pwd_help_texts": password_validators_help_texts(),
    }

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("confirmPassword")

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        region = request.POST.get("region")
        dob_str = request.POST.get("date_of_birth")

        if password != password2:
            ctx["custom_message"] = "Hasła nie są takie same."
            return render(request, "signup.html", ctx)

        try:
            date_of_birth = datetime.date.fromisoformat(dob_str)
        except ValueError:
            ctx["custom_message"] = "Niepoprawna data urodzenia."
            return render(request, "signup.html", ctx)

        if User.objects.filter(username=username).exists():
            ctx["custom_message"] = "Nazwa użytkownika jest już zajęta."
            return render(request, "signup.html", ctx)

        email = User.objects.normalize_email(email)
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            region=region,
            date_of_birth=date_of_birth,
        )

        try:
            validate_password(password, user=user)
        except ValidationError as e:
            ctx["custom_message"] = "\n".join(e.messages)
            return render(request, "signup.html", ctx)
        user.set_password(password)

        try:
            user.full_clean(validate_unique=False)
        except ValidationError as e:
            ctx["custom_message"] = "\n".join(msg for msgs in e.message_dict.values() for msg in msgs)
            return render(request, "signup.html", ctx)

        try:
            with transaction.atomic():
                user.save()
                group, _ = Group.objects.get_or_create(name='user')
                user.groups.add(group)
        except IntegrityError:
            # Caused by duplicate email, do not leak that information
            pass

        return redirect("../signin/")

    return render(request, "signup.html", ctx)


def signin(request):
    if request.user.is_authenticated:
        return render(request, "signin.html", {
            "custom_message": f"Jesteś zalogowany jako {request.user.username}. Przed ponownym zalogowaniem wyloguj się."
        })

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, "signin.html", {
                "custom_message": "Login lub hasło jest niepoprawne."
            })

        login(request, user)
        return redirect("/")

    return render(request, "signin.html")


@login_required(login_url='../signin')
def profile(request):
    ctx = {
        "region_choices": User._meta.get_field('region').choices,
    }

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        region = request.POST.get("region")
        dob_str = request.POST.get("date_of_birth")
        uploaded = request.FILES.get("profile_image")

        if dob_str:
            try:
                date_of_birth = datetime.date.fromisoformat(dob_str)
            except ValueError:
                ctx["custom_message"] = "Niepoprawna data urodzenia."
                return render(request, "profile.html", ctx)
            else:
                request.user.date_of_birth = date_of_birth

        if uploaded:
            request.user.profile_image = uploaded

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.region = region

        try:
            request.user.full_clean()
        except ValidationError as e:
            ctx["custom_message"] = "\n".join(msg for msgs in e.message_dict.values() for msg in msgs)
            return render(request, "profile.html", ctx)

        request.user.save(
            update_fields=['first_name', 'last_name', 'region', 'date_of_birth', 'profile_image']
        )
        ctx["custom_message"] = "Profil został zaktualizowany."

    return render(request, "profile.html", ctx)


@login_required(login_url='../signin')
def change_password(request):
    ctx = {
        "pwd_help_texts": password_validators_help_texts(),
    }

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(old_password):
            ctx["custom_message"] = "Niepoprawne stare hasło."
            return render(request, 'changepassword.html', ctx)

        if new_password1 != new_password2:
            ctx["custom_message"] = "Hasła nie są takie same."
            return render(request, 'changepassword.html', ctx)

        try:
            validate_password(new_password1, user=request.user)
        except ValidationError as e:
            ctx["custom_message"] = "\n".join(e.messages)
            return render(request, 'changepassword.html', ctx)

        request.user.set_password(new_password1)
        request.user.save()
        messages.success(request, "Hasło zmienione poprawnie!")
        ctx["custom_message"] = "Twoje hasło zostało zmienione!"
        return render(request, 'changepassword.html', ctx)

    return render(request, 'changepassword.html', ctx)


@login_required(login_url='../signin')
def signout(request):
    logout(request)
    return redirect("/")
