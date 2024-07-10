from django.shortcuts import render
import datetime
from django.contrib import messages
from accounts.models import User
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from mainSite.models import Post
from hintBase.models import Problem, ProblemHint


# Create your views here.



def signup(request):
    
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password0 = request.POST.get("password")
        password1 = request.POST.get("confirmPassword")
        
        name = request.POST.get("name")
        surname = request.POST.get("surname")
        date_of_birth = request.POST.get("date_of_birth")
        region = request.POST.get("region")
        image = request.POST.get("profile_image")
        
        if User.objects.filter(email=email).exists():
            print("email exists, redirecting to signup")
            return render(request, "signup.html", {"custom_message": "Konto z takim adresem e-mail już istnieje."})
        if User.objects.filter(username=username).exists():
            print("username exists, redirecting to signup")
            return render(request, "signup.html", {"custom_message": "Konto z taką nazwą użytkownika już istnieje."})
        
       
        try:
            # Attempt to parse the date (modify format string as needed)
            datetime.datetime.strptime(date_of_birth, '%Y-%m-%d')
        except ValueError:
            # If invalid format, assign "default_date" and add an error message
            print("Brak/ data essy nie ma")
            date_of_birth = datetime.date.today()
        
        
        
        print(password0, password1)
        if password0 != password1:
            return render(request, "signup.html", {"custom_message": "Hasła nie są takie same."})
        
        newUser = User.objects.create_user(username=username, email=email, password=password0)
        
        newUser.name = name
        newUser.surname = surname
        newUser.date_of_birth = date_of_birth
        newUser.region = region
    
        group, created = Group.objects.get_or_create(name='user')
        newUser.groups.add(group)
        newUser.save()
        
        print("success, redirecting to signin")
        return redirect("../signin/")
        
        
        
    return render(request, "signup.html")

def signin(request):
    
    if request.user.is_authenticated:
            return render(request, "signin.html", {"custom_message": f"Jesteś zalogowany jako {request.user.username}. Musisz się wylogować, aby zalogować się ponownie."})
    
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
    if request.method =="POST":
        new_user = User(
                username=request.user.username,  # Preserve original username for security
                email=request.user.email,        # Preserve original email for security
                name=request.POST.get('name'),
                surname=request.POST.get('surname'),
                region=request.POST.get('region'),
                date_of_birth=request.POST.get('date_of_birth'),
                problem_counter=request.user.problem_counter  # Preserve original problem counter
            )
        print(new_user.date_of_birth)
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
            print("Brak/hujowa data essy nie ma")
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
    print(user_belongs_to_moderator_group)
    messages["user_belongs_to_moderator_group"] = user_belongs_to_moderator_group
    return render(request, "profile.html", messages)

def public_profile(request, username):
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
            return render(request, 'changepassword.html', {"custom_message": "Hasło zostało zmienione"}) # Adjust to your success page URL

    return render(request, 'changepassword.html')  # Adjust to your template name

@login_required(login_url='../signin')
def signout(request):
    logout(request)
    return redirect("/")

@login_required(login_url='../signin')
def zarzadzanie(request):
    messages={}
    all_users = User.objects.all()
    moderator_group = Group.objects.get(name='Moderator')
    moderator_users = moderator_group.user_set.all()

    if request.user.is_staff == False:
        return redirect("/")
    if request.method == 'POST':

        if request.POST.get("delete") == "True":
            username = request.POST.get("user_username")
            try:
                user_to_delete =User.objects.get(username=username)
            except:
                return render(request, "zarzadzanie.html", {'all_users': all_users, 'moderator_users': moderator_users,
                                                            "custom_message": f"Konto o podanej nazwie użytkownika nie istnieje"})

            print(user_to_delete)
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
        print(author_ids)
        authors = []
        for author_id in author_ids:
            print(author_id)
            try:
                author = User.objects.get(username=author_id)
                authors.append(author)
            except User.DoesNotExist:
                return redirect("/zarzadzanie/", {"custom_message": "Uzytkownik o podanym ID nie istnieje"})
        print(authors)
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
    
