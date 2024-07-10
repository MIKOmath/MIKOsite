from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import random
from taggit.managers import TaggableManager
class Problem(models.Model):
    
    problem_id = models.AutoField(primary_key=True)
    latex_code = models.TextField()

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='problem_images/', blank=True, null=True)
    difficulty = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(11)]
    )
    date = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True) 
    verified = models.BooleanField(default=False, blank=True, null=True)


    tags = TaggableManager()

    def __str__(self):
        if self.author is not None:
            return f'Problem by {self.author.username}, problem id: {self.problem_id}'
        else:
            return f'Problem, problem id: {self.problem_id}, no author'

class ProblemHint(models.Model):
    hintId = models.AutoField(primary_key=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    hints = models.TextField()  # Serialized list of hints
    latex_solution = models.TextField()
    date = models.DateField(blank=True, null=True)  # Date field
    time = models.TimeField(blank=True, null=True)  # Time field


    def __str__(self):
        return f'Hint for Problem {self.problem.problem_id} by {self.author.username}'

class Review(models.Model):
    current_rating = models.FloatField(blank=True, null=True, default=0)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, null=True, blank=True)
    ratings = models.JSONField(default=dict, blank=True, null=True)

    def update_rating(self):
        new_value = 0
        amount = len(self.ratings)
        for rating in self.ratings:
            new_value += float(self.ratings[rating])
        new_value = round(new_value/amount, 2)
        self.current_rating = new_value
        self.problem.difficulty = new_value
        self.save()
        self.problem.save()

    def add_rating(self, key, value):
        if not isinstance(value, int):
            raise ValueError("Key must be a string and value must be an integer.")
        if not User.objects.filter(username=key).exists():
            raise ValueError(f"No User with username '{key}' found.")

        updated = False
        for rating in self.ratings:
            if rating == key:
                self.ratings[rating] = value
                updated = True
                break
        # self.ratings.append({"username": key, "value": value})
        self.ratings[key] = value
        self.save()
        return "Rating added"

    def __str__(self):
        return f'({self.current_rating}) Review for Problem {self.problem.problem_id} by {self.problem.author.username}'


