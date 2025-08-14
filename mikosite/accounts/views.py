import datetime
from django.shortcuts import render
from django.contrib import messages
from accounts.models import User
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from mainSite.models import Post
from hintBase.models import Problem, ProblemHint
from django.http import HttpResponse
from .forms import UserCreationForm, ProfileChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password0 = request.POST.get("password")
        password1 = request.POST.get("confirmPassword")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        region = request.POST.get("region")
        date_of_birth = request.POST.get("date_of_birth").strip()

        print(date_of_birth)
        print(type(date_of_birth))

        # try:
        #     date_of_birth = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        # except ValueError:
        #     # If user may submit other formats, you can try multiple patterns (see next snippet)
        #     return render(request, "signup.html", {"custom_message": "Niepoprawny format daty. Użyj RRRR-MM-DD."})


        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"custom_message": "Konto z takim adresem e-mail już istnieje."})
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"custom_message": "Konto z taką nazwą użytkownika już istnieje."})


        form = UserCreationForm(
            data={
                'username': username,
                'email': email,
                'password': password0,
                'password_confirmation': password1,
                'date_of_birth': date_of_birth,
                'region': region,
            }
        )

        if password0 != password1:
            return render(request, "signup.html", {"custom_message": "Hasła nie są takie same."})

        

        if form.is_valid():

            newUser = User.objects.create_user(
                username=username,
                email=email,
                password=password0,
                date_of_birth=date_of_birth,
                region=region,
            )

            newUser.first_name = first_name
            newUser.last_name = last_name

            group, created = Group.objects.get_or_create(name='user')
            newUser.groups.add(group)
            newUser.save()

            return redirect("../signin/", {"custom_message": "Konto zostało utworzone. Możesz się zalogować."})
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    print(f"{field}: {err}")
            return render(request, "signup.html", {"custom_message": "Niepoprawne dane. Sprawdź formularz."})
            
        

    return render(request, "signup.html", status=200)


def signin(request):
    if request.user.is_authenticated:
        return render(request, "signin.html", {
            "custom_message": f"Jesteś zalogowany jako {request.user.username}. Musisz się wylogować, aby zalogować się ponownie."}, status=403)

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "signin.html", {"custom_message": "Login laub hasło nie jest poprawne"})
    return render(request, "signin.html")


@login_required(login_url='../signin')
def profile(request):
    messages = {}
    if request.method == "POST":
        new_user = User.objects.filter(username=request.user.username).first()

        form = ProfileChangeForm(
            data={
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'region': request.POST.get('region'),
                'date_of_birth': request.POST.get('date_of_birth'), 
            }
        )

        if form.is_valid():
            changes_detected = (
                request.user.first_name != form.cleaned_data['first_name'] or
                request.user.last_name != form.cleaned_data['last_name'] or
                request.user.region != form.cleaned_data['region'] or
                request.user.date_of_birth != form.cleaned_data['date_of_birth']
            )

            if changes_detected:
                new_user.first_name = form.cleaned_data['first_name']
                new_user.last_name = form.cleaned_data['last_name']
                new_user.region = form.cleaned_data['region']
                new_user.date_of_birth = form.cleaned_data['date_of_birth']
                new_user.save()
            return render(request, "profile.html", {"custom_message": "Zmiany zostały zapisane"})
        else:
            return render(request, "profile.html", {"custom_message": "Niepoprawne dane. Sprawdź formularz."})
            # Access to errors to see specific validation errors: form.errors
        # else:
        #     return render(request, "profile.html", {"custom_message": "Zadnych zmian nie ma"})
    user_belongs_to_moderator_group = request.user.groups.filter(name='Moderator').exists()

    messages["user_belongs_to_moderator_group"] = user_belongs_to_moderator_group
    return render(request, "profile.html", messages)


@login_required(login_url='../signin')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        # Validate form data
        if not request.user.check_password(old_password):
            return render(request, 'changepassword.html', {"custom_message": "Niepoprawne stare hasło"})
        elif new_password1 != new_password2:
            return render(request, 'changepassword.html', {"custom_message": "Hasła nie są takie same"})
        else:
            # Change password and redirect to success page
            request.user.set_password(new_password1)
            request.user.save()
            messages.success(request, "Password changed successfully!")
            return render(request, 'changepassword.html',
                          {"custom_message": "Hasło zostało zmienione"})  # Adjust to your success page URL

    return render(request, 'changepassword.html')  # Adjust to your template name


@login_required(login_url='../signin')
def signout(request):
    logout(request)
    return redirect("/")
