from django.shortcuts import render
import datetime
from django.contrib import messages
from .models import User
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from mainSite.models import Post
from hintBase.models import Problem, ProblemHint
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from datetime import date


def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        date_of_birth = request.POST.get("date_of_birth")
        region = request.POST.get("region")

        if password != confirm_password:
            return render(request, "signup.html", {"custom_message": "Podane hasła się różnią."})

        parsed_dob = parse_date(date_of_birth)
        if not parsed_dob:
            return render(request, "signup.html", {"custom_message": "Data nie jest poprawna."})

        if calculate_age(parsed_dob) < 13:
            return render(request, "signup.html", {"custom_message": "Musisz mieć co najmniej 13 lat, "
                                                                     "aby się zarejestrować."})

        try:
            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                name=name,
                surname=surname,
                date_of_birth=parsed_dob,
                region=region,
            )
            new_user.full_clean(validate_unique=False)
            new_user.save()

            return redirect("signin")

        except ValidationError as e:
            return render(request, "signup.html", {"custom_message": str(e)})

    return render(request, "signup.html")

def signin(request):
    if request.user.is_authenticated:
        return render(request, "signin.html", {
            "custom_message": f"Już jesteś zalogowany jako {request.user.username}."})

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "signin.html", {"custom_message": "Login lub hasło nie jest poprawne"})
    return render(request, "signin.html")


@login_required(login_url='../signin')
def profile(request):
    messages = {}
    if request.method == "POST":
        new_user = User(
            username=request.user.username,  # Preserve original username for security
            email=request.user.email,  # Preserve original email for security
            name=request.POST.get('name'),
            surname=request.POST.get('surname'),
            region=request.POST.get('region'),
            date_of_birth=request.POST.get('date_of_birth'),
            problem_counter=request.user.problem_counter  # Preserve original problem counter
        )

        changes_detected = False
        try:
            # Attempt to parse the date (modify format string as needed)
            datetime.datetime.strptime(new_user.date_of_birth, '%Y-%m-%d')
            for field in ['name', 'surname', 'region', 'date_of_birth']:
                original_value = getattr(request.user, field)
                new_value = getattr(new_user, field)
                if original_value != new_value:
                    changes_detected = True
                    break
        except ValueError:
            # If invalid format, assign "default_date" and add an error message
            for field in ['name', 'surname', 'region']:
                original_value = getattr(request.user, field)
                new_value = getattr(new_user, field)
                if original_value != new_value:
                    changes_detected = True
                    break

        if changes_detected:
            request.user.name = new_user.name
            request.user.surname = new_user.surname
            request.user.region = new_user.region
            request.user.date_of_birth = new_user.date_of_birth
            request.user.save()

            return render(request, "profile.html", {"custom_message": "Zmiany zostały zapisane"})
        else:
            return render(request, "profile.html", {"custom_message": "Zadnych zmian nie ma"})
    user_belongs_to_moderator_group = request.user.groups.filter(name='Moderator').exists()

    messages["user_belongs_to_moderator_group"] = user_belongs_to_moderator_group
    return render(request, "profile.html", messages)


def public_profile(request, username):
    return HttpResponse("Update soon :))")
    user = User.objects.get(username=username)

    parameters_to_pass = {}

    _username = username
    name = user.name
    surname = user.surname
    user_problems = Problem.objects.filter(author=user)
    user_hints = ProblemHint.objects.filter(author=user)

    parameters_to_pass["problems"] = user_problems
    parameters_to_pass["hints_ids"] = [hint.problem.problem_id for hint in user_hints]
    parameters_to_pass["surname"] = surname
    parameters_to_pass["name"] = name
    parameters_to_pass["username"] = _username

    return render(request, "publicprofile.html", parameters_to_pass)


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


@login_required(login_url='../signin')
def zarzadzanie(request):
    all_users = User.objects.all()
    moderator_group = Group.objects.get(name='Moderator')
    moderator_users = moderator_group.user_set.all()

    if not request.user.is_staff:
        return redirect("/")
    if request.method == 'POST':

        if request.POST.get("delete") == "True":
            username = request.POST.get("user_username")
            try:
                user_to_delete = User.objects.get(username=username)
            except:
                return render(request, "zarzadzanie.html", {'all_users': all_users, 'moderator_users': moderator_users,
                                                            "custom_message": "Konto o podanej nazwie użytkownika nie istnieje"})

            user_to_delete.delete()
            return render(request, "zarzadzanie.html", {'all_users': all_users, 'moderator_users': moderator_users,
                                                        "custom_message": f"Usunęto konto {user_to_delete}"})

        if request.POST.get('title') == '':
            request.session['custom_message'] = "Tytuł nie może być pusty"
            return redirect("/zarzadzanie/")
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        author_ids = request.POST.getlist('authors')
        file = request.FILES.get('file')
        images = request.FILES.getlist('images')
        text_field_1 = request.POST.get('text_field_1')
        text_field_2 = request.POST.get('text_field_2')

        # Verify if the user exists
        authors = []
        for author_id in author_ids:
            try:
                author = User.objects.get(username=author_id)
                authors.append(author)
            except User.DoesNotExist:
                return redirect("/zarzadzanie/", {"custom_message": "Uzytkownik o podanym ID nie istnieje"})

        # Create the post
        post = Post(
            title=title,
            subtitle=subtitle,
            text_field_1=text_field_1,
            text_field_2=text_field_2,
        )

        post.save()
        post.authors.set(authors)
        # If file is uploaded, save it
        if file:
            post.file = file

        # If images are uploaded, save them
        if images:
            for image in images:
                post.images.create(image=image)
        post.save()

        request.session['custom_message'] = "Post został utworzony"
        return redirect('/zarzadzanie/')

    return render(request, "zarzadzanie.html", {'all_users': all_users, 'moderator_users': moderator_users})
