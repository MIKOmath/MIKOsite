# accounts/forms.py
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import REGION_CHOICES
from .validators import validate_not_future_date, validate_min_age_13
User = get_user_model()


class UserCreationForm(forms.Form):
    username =              forms.CharField(max_length=150, required=True)
    email =                 forms.EmailField(required=True)
    password =              forms.CharField(widget=forms.PasswordInput, required=True)
    password_confirmation = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")
    date_of_birth =         forms.DateField( 
                                validators=[
                                    validate_not_future_date,       
                                    validate_min_age_13,   # For now let's assume that the 
                                    # minimum age is 13 (7-8th year of school)
                                ],
                                required=True,
                            )
    region =                forms.ChoiceField(choices=REGION_CHOICES, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")

        if password and password_confirmation and password != password_confirmation:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

class ProfileChangeForm(forms.Form):

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    date_of_birth =         forms.DateField( 
                                validators=[
                                    validate_not_future_date,       
                                    validate_min_age_13,   # For now let's assume that the 
                                    # minimum age is 13 (7-8th year of school)
                                ],
                            )
    region =                forms.ChoiceField(choices=REGION_CHOICES)

