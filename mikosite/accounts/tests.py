from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from unittest.mock import patch
from .models import User, CustomUserManager
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import datetime
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError




class CustomUserManagerTests(TestCase):
    def setUp(self):
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepass123',
            'name': 'Test',
            'surname': 'User'
        }

        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='existing123',
            name='Existing',
            surname='User'
        )

    def test_create_user_success(self):
        """Test successful user creation with proper data"""
        user = User.objects.create_user(**self.valid_user_data)

        self.assertIsNotNone(user.pk)  # Verify user was saved to database
        self.assertEqual(user.username, self.valid_user_data['username'])
        self.assertEqual(user.email, self.valid_user_data['email'])
        self.assertEqual(user.name, self.valid_user_data['name'])
        self.assertEqual(user.surname, self.valid_user_data['surname'])
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password(self.valid_user_data['password']))


    def test_create_user_no_email(self):
        """Test user creation fails when email is not provided"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = ''

        with self.assertRaises(ValueError) as context:
            User.objects.create_user(**invalid_data)

        self.assertIn('Adres e-mail jest wymagany', str(context.exception))

    def test_create_user_duplicate_username(self):
        """Test user creation fails with duplicate username"""
        duplicate_data = self.valid_user_data.copy()
        duplicate_data['username'] = 'existinguser'

        with self.assertRaises(ValidationError) as context:
            User.objects.create_user(**duplicate_data)

        self.assertIn('ta nazwa użytkownika już jest zajęta.', str(context.exception).lower())

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email returns generic error"""
        duplicate_data = self.valid_user_data.copy()
        duplicate_data['email'] = 'existing@example.com'

        with self.assertRaises(ValidationError) as context:
            User.objects.create_user(**duplicate_data)

        self.assertIn('rejestracja się nie powiodła. sprawdź dane jeszcze raz.', str(context.exception).lower())
        self.assertNotIn('existing@example.com', str(context.exception))

    def test_create_superuser_success(self):
        """Test successful superuser creation"""
        superuser = User.objects.create_superuser(**self.valid_user_data)

        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.username, self.valid_user_data['username'])
        self.assertEqual(superuser.name, self.valid_user_data['name'])
        self.assertEqual(superuser.surname, self.valid_user_data['surname'])

    def test_create_user_blank_fields(self):
        """Test user creation fails with blank required fields"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['name'] = ''
        invalid_data['surname'] = ''

        with self.assertRaises(ValidationError) as context:
            User.objects.create_user(**invalid_data)

        error_dict = eval(str(context.exception)[2:-2])  # Convert string representation to dict
        self.assertIn('name', error_dict)
        self.assertIn('surname', error_dict)

    def test_create_user_no_required_fields(self):
        """Test user creation fails with blank required fields"""
        invalid_data = self.valid_user_data.copy()
        del invalid_data['name']
        del invalid_data['surname']

        with self.assertRaises(ValidationError) as context:
            User.objects.create_user(**invalid_data)

    def test_create_user_with_minimal_fields(self):
        """Test user creation with only the minimal required fields"""
        minimal_data = {
            'username': 'minimaluser',
            'email': 'minimal@example.com',
            'password': 'minimal123',
            'name': 'Minimal',
            'surname': 'User'
        }

        user = User.objects.create_user(**minimal_data)
        self.assertIsNotNone(user.pk)
        self.assertEqual(user.username, minimal_data['username'])

    def test_invalid_region(self):
        """
        Attempt at creating new user with invalid region. Expected to raise error.
        """
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                username="testuser",
                email="testuser@example.com",
                password="testpassword",
                region="InvalidRegion",
                name="Valid",
                surname="Valid",
            )

    def test_valid_region(self):
        try:
            user = User.objects.create_user(
                username="testuser",
                email="testuser@example.com",
                password="testpassword",
                region="pomorskie",
                name="Valid",
                surname="Valid",
            )
            self.assertIsNotNone(user)
        except ValidationError:
            self.fail("User creation failed for a valid region with valid data.")


class SignupViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')

    def test_signup_successful(self):
        """Test a successful user signup."""
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2000-01-01',
            'region': 'lubelskie',
        })

        user = User.objects.filter(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'testuser@example.com')

        self.assertRedirects(response, reverse('signin'))

    def test_signup_password_mismatch(self):
        """Test password mismatch during signup."""
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'differentpassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2000-01-01',
            'region': 'lubelskie',
        })

        # Ensure the user is not created
        user_count = User.objects.count()
        self.assertEqual(user_count, 0)
        # Check if the correct error message is displayed
        self.assertContains(response, "Podane hasła się różnią.")

    def test_signup_invalid_date_of_birth(self):
        """Test invalid date of birth during signup."""
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': 'invalid-date',
            'region': 'lubelskie',
        })

        # Ensure the user is not created
        user_count = User.objects.count()
        self.assertEqual(user_count, 0)

        # Check if the correct error message is displayed
        self.assertContains(response, "Data nie jest poprawna.")


    def test_signup_existing_email(self):
        """Test signup with an already registered email."""
        # Create a user with the same email
        User.objects.create_user(
            username='existinguser',
            email='testuser@example.com',
            password='password123',
            name="good",
            date_of_birth="2000-01-02",
            surname="USER",
        )

        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2000-01-01',
            'region': 'lubelskie',
        })

        # Ensure the user is not created
        user_count = User.objects.filter(username='testuser').count()
        self.assertEqual(user_count, 0)

        # Check if the correct error message is displayed
        self.assertContains(response, "Rejestracja się nie powiodła. Sprawdź dane jeszcze raz.")

    def test_signup_invalid_region(self):
        """Test signup with an invalid region."""
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2000-01-01',
            'region': 'InvalidRegion',
        })

        # Ensure the user is not created
        user_count = User.objects.count()
        self.assertEqual(user_count, 0)

        # Check if the correct error message is displayed
        self.assertContains(response, "Wybierz poprawne województwo. Dostępne opcje")

    def test_signup_missing_required_fields(self):
        """Test signup with missing required fields."""
        response = self.client.post(self.signup_url, {
            'username': '',
            'email': '',
            'password': '',
            'confirmPassword': '',
            'name': '',
            'surname': '',
            'date_of_birth': '',
            'region': '',
        })

        user_count = User.objects.count()
        self.assertEqual(user_count, 0)
    def test_signup_multiple_instances_of_bad_data(self):
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2000-01-AS',
            'region': 'InvalidRegion',
        })

        user_count = User.objects.count()
        self.assertEqual(user_count, 0)
        self.assertContains(response, "Data nie jest poprawna.")

    def test_signup_age_low(self):
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2020-01-11',
            'region': 'małopolskie',
        })

        user_count = User.objects.count()
        self.assertEqual(user_count, 0)
        self.assertContains(response, "Musisz mieć co najmniej 13 lat, aby się zarejestrować.")

    def test_signup_age_good(self):
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'securepassword123',
            'confirmPassword': 'securepassword123',
            'name': 'Test',
            'surname': 'User',
            'date_of_birth': '2002-01-11',
            'region': 'małopolskie',
        })

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)



