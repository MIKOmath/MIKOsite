from django.shortcuts import render, HttpResponse
from django.contrib import messages
from accounts.models import User
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.conf import settings
from .models import Problem, ProblemHint, Review
from taggit.models import Tag
from fuzzywuzzy import fuzz
from datetime import datetime
from pytz import timezone
import pytz
from django.db.models import Q


# Create your views here.


# Index view: Displays the list of problems with filtering options
def index(request):
    # Retrieve all problems in reverse order
    all_problems = reversed(Problem.objects.all())
    
    # Check if the user belongs to the 'Moderator' group
    user_belongs_to_moderator_group = request.user.groups.filter(name='Moderator').exists()
    
    # Get all tag names
    tags = [tag.name for tag in Tag.objects.all()]
    
    if request.method == 'POST':
        tags_to_filter = set(request.POST.getlist('tags_to_filter'))
        diffStr = str(request.POST.get('difficulty'))
        search = str(request.POST.get("search"))
        print(search)
        if len(diffStr) != 0:
            ranges = [int(x) for x in diffStr.split(',')]
            query = Q()

            for value in ranges:
                query |= Q(difficulty__gte=value, difficulty__lt=value + 1)
            filtered_problems = reversed(Problem.objects.filter(query))
        else:
            filtered_problems = all_problems
        if tags_to_filter:
            filtered_problems = [
                problem for problem in filtered_problems
                if tags_to_filter.issubset(set(problem.tags.names()))
            ]
        if search != "":
            filtered_problems = [
                problem for problem in filtered_problems
                if search in problem.latex_code
            ]

        return render(request, 'index1.html', {
            "all_problems": filtered_problems,
            "user_belongs_to_moderator_group": user_belongs_to_moderator_group, 
            "tags": tags
        })

    return render(request, 'index1.html', {
        "all_problems": all_problems, 
        "user_belongs_to_moderator_group": user_belongs_to_moderator_group, 
        "tags": tags
    })


# Add Problem view: Allows authenticated users to add a new problem
@login_required(login_url='../../signin')
def addproblem(request):
    tags = [tag.name for tag in Tag.objects.all()]

    if request.method == 'POST':
        latex_code = request.POST.get('latex_code')
        source = request.POST.get('source')
        image = request.FILES.get('image')
        selected_tags = request.POST.getlist('selected_tags')

        try:
            difficulty = int(request.POST.get('difficulty'))
            if not (0 <= difficulty <= 11):
                raise ValueError
        except (ValueError, TypeError):
            return render(request, 'addproblem.html', {
                "custom_message": "Coś jest nie tak z trudnością. Musi być liczbą całkowitą między 0 a 10.",
                "tags": tags,
                "confirm_key": "False"
            })

        warsaw_timezone = timezone('Europe/Warsaw')

        # Get current time in Warsaw timezone
        current_time = datetime.now(warsaw_timezone)

        # Extract date and time
        current_date = current_time.date()
        current_time = current_time.time()


        problem = Problem(
            latex_code=latex_code,
            source=source,
            image=image,
            difficulty=difficulty,
            author=request.user,
            date = current_date,
            time = current_time,
        )

        confirm_key = request.POST.get('confirm_key')

        # Check for similar problems if confirmation key is not set
        if confirm_key is None:
            for tag in selected_tags:
                if tag not in tags:
                    return render(request, 'addproblem.html', {
                        "custom_message": f"Tag {tag} nie istnieje",
                        "confirm_key": "False",
                        "tags": tags
                    })
            similar_problems = [
                selected_Problem for selected_Problem in Problem.objects.all()
                if fuzz.ratio(selected_Problem.latex_code, latex_code) > 64
            ]
            if similar_problems:
                return render(request, 'addproblem.html', {
                    "tags": tags,
                    "custom_message": "Możliwe, że to zadanie już jest w bazie zadań, sprawdź czy dalej chcesz dodać to zadanie. Pamiętaj o zaznaczeniu tagów zadania.",
                    "similar_problems": similar_problems,
                    "confirm_key": "True",
                    "problem": problem
                })

        if confirm_key == "Usuń":
            return render(request, 'addproblem.html', {
                "custom_message": "Usunięto zadanie.",
                "confirm_key": "False",
                "tags": tags
            })

        problem.save()
        problem.tags.add(*selected_tags)
        problem.save()

        request.user.problem_counter += 1
        request.user.save()

        return render(request, 'addproblem.html', {
            "custom_message": f"Zadanie zostało dodane, id zadania: {problem.problem_id}",
            "confirm_key": "False",
            "tags": tags
        })

    return render(request, 'addproblem.html', {
        "tags": tags,
        "confirm_key": "False"
    })


# View Problem view: Displays a specific problem and its hints
def view_problem(request, problem_id):
    problem = get_object_or_404(Problem, problem_id=problem_id)
    hinty = ProblemHint.objects.filter(problem=problem, verified=True)
    try:
        reviews = Review.objects.get(problem=problem,)
    except:
        reviews = Review(current_rating=problem.difficulty, problem=problem)
        reviews.save()

    is_admin = request.user.is_superuser

    if request.user.is_authenticated:
        if request.method == "POST":
            if request.POST.get("delhandeler") == "delete":
                if is_admin==True:
                    problem.delete()
                    return redirect("/bazahintow/")
            else:
                try:
                    proposed = int(request.POST.get("difficulty"))
                except:
                    return HttpResponse("Difficuty must be an integer")
                reviews.add_rating(request.user.username, proposed)
                reviews.update_rating()

    return render(request, 'viewproblem.html', {
        "problem": problem,
        "user": request.user,
        "hinty": hinty,
        "is_admin": is_admin,
        "rating": reviews.current_rating
    })


# Add Solution view: Allows authenticated users to add a solution to a problem
@login_required(login_url='../signin')
def add_solution(request, problem_id):


    problem = get_object_or_404(Problem, problem_id=problem_id)

    warsaw_timezone = timezone('Europe/Warsaw')

    # Get current time in Warsaw timezone
    current_time = datetime.now(warsaw_timezone)

    # Extract date and time
    current_date = current_time.date()
    current_time = current_time.time()


    if request.method == 'POST':
        hints = "\n".join([value for key, value in request.POST.items() if key.startswith('hint')])

        problemhint = ProblemHint(
            problem=problem,
            author=request.user,
            hints=hints,
            latex_solution=request.POST.get('solution'),
            date=current_date,
            time=current_time,
        )
        problemhint.save()
        return redirect(f"/bazahintow/view_problem/{problem_id}/")

    return render(request, 'addsolution.html', {"problem": problem})


# Verify Solutions view: Allows moderators to verify or delete solutions
@login_required(login_url='../../signin')
def verifysolutions(request):
    if not request.user.groups.filter(name='Moderator').exists():
        return redirect("/")



    if request.method == 'POST':
        if 'delete_solution' in request.POST:
            hint_to_delete = ProblemHint.objects.get(hintId=request.POST['delete_solution'])
            hint_to_delete.delete()
        elif 'verify_solution' in request.POST:
            hint_to_verify = ProblemHint.objects.get(hintId=request.POST['verify_solution'])
            hint_to_verify.verified = True
            hint_to_verify.save()

    solutions_toverify = ProblemHint.objects.filter(verified=False)
    problems_toverify = Problem.objects.filter(verified=False) # Add functionality to remove unferified problems. 


    return render(request, 'verifysolutions.html', {"solutions_toverify": solutions_toverify, "problems_toverify" : problems_toverify})