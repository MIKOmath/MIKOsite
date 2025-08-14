from django.test import TestCase, Client
from .validators import validate_not_future_date, validate_min_age_13
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import datetime
from .forms import UserCreationForm, ProfileChangeForm
User = get_user_model()

class ValidatorsTests(TestCase):
    def test_validate_not_future_date(self):
        """
        Test that `validate_not_future_date` correctly handles future dates.
        """
        date_in_future = date.today() + timedelta(days=1)
        
        # Assert that ValidationError is raised
        with self.assertRaises(ValidationError):
            validate_not_future_date(date_in_future)

    def test_validate_min_age_13(self):
        """
        Test that `validate_min_age_13` correctly handles ages.
        """
        date_just_under_13 = timezone.now().date() - relativedelta(years=13) + relativedelta(days=1)
        with self.assertRaises(ValidationError) as cm:
            validate_min_age_13(date_just_under_13)
        
        try:
            date_exactly_13 = timezone.now().date() - relativedelta(years=13)
            validate_min_age_13(date_exactly_13)

            date_just_over_13 = timezone.now().date() - relativedelta(years=13, days=1)
            validate_min_age_13(date_just_over_13)

            date_much_older = timezone.now().date() - relativedelta(years=20)
            validate_min_age_13(date_much_older)
            
        except ValidationError:
            self.fail("validate_min_age_13() raised ValidationError unexpectedly for a valid age.")


class AccountsGeneralTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "1qa2wsDE#"
        self.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password=self.password,
            date_of_birth=timezone.now().date(),
            region="MZ",  
        )
        self.user.first_name = "Jan"
        self.user.last_name = "Kowalski"
        self.user.save()

    # ========== Signup ==========

    def test_signup_success_creates_user_and_redirects(self):
        data = {
            "first_name": "Name",
            "last_name": "Lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password": "qwertyuiop",
            "confirmPassword": "qwertyuiop",
            "region": "PM",
            "date_of_birth": "2002-05-10",
        }
        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username="test123456").exists())
        new_user = User.objects.get(username="test123456")
        self.assertTrue(new_user.groups.filter(name="user").exists())
        self.assertEqual(new_user.region, "PM")
        self.assertEqual(str(new_user.date_of_birth), "2002-05-10")
        self.assertEqual(new_user.first_name, "Name")
        self.assertEqual(new_user.last_name, "Lastname")

    def test_signup_duplicate_email(self):
        User.objects.create_user(
            username="test123456",
            email="test@miko.com",
            password="qwertyuiop",
            date_of_birth=timezone.now().date(),   # Expected not to trigger User form for min age
            region="MZ",
        )
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password": "qwertyuiop",
            "confirmPassword": "qwertyuiop",
            "region": "PM",
            "date_of_birth": "2002-05-10",
        }
        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Konto z takim adresem e-mail już istnieje.")

    def test_signup_duplicate_username(self):
        User.objects.create_user(
            username="testExisting",
            email="test@miko.com",
            password="qwertyuiop",
            date_of_birth=timezone.now().date(),   # Expected not to trigger User form for min age
            region="MZ",
        )
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "testExisting",
            "email": "testNew@miko.com",
            "password": "qwertyuiop",
            "confirmPassword": "qwertyuiop",
            "region": "PM",
            "date_of_birth": "2002-05-10",
        }

        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Konto z taką nazwą użytkownika już istnieje.")

    def test_signup_password_mismatch(self):
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "QwertyuioP",  # Mismatch 
            "region": "PM",
            "date_of_birth": "2002-05-10",
        }
        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200)
        user = User.objects.filter(username="abc").first()
        self.assertTrue(user is None)
        self.assertContains(resp, "Hasła nie są takie same.")

    def test_signup_invalid_dob_user_not_created(self):
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "qwertyuiop",   
            "region": "PM",
            "date_of_birth": "invalid-date",  # Invalid date
        }
        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200) # User provided invalid date, so form is not valid
        self.assertFalse(User.objects.filter(username="todayout").exists())


    # ========= Signin ==========

    def test_signin_success_authenticates_session(self):
        resp = self.client.post("/signin/", {"username": "u1", "password": self.password}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.wsgi_request.user.is_authenticated)

    def test_signin_wrong_password_keeps_anonymous(self):
        resp = self.client.post("/signin/", {"username": "u1", "password": "wrong"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    # Additional test for signin with wrong username 

    # --- Signout ---

    def test_signout_logs_out(self):
        self.client.login(username="u1", password=self.password)
        resp = self.client.get("/signout/", follow=True)
        self.assertEqual(resp.status_code, 200)
        resp2 = self.client.get("/profile/")
        self.assertEqual(resp2.status_code, 302)

    def test_signup_redirect_location_after_success(self):
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "qwertyuiop",   
            "region": "PM",
            "date_of_birth": "2002-05-10",
        }

        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp["Location"].endswith("/signin/"))

    def test_signup_invalid_region_code_rejected(self):
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "qwertyuiop",   
            "region": "XX",
            "date_of_birth": "2002-05-10",
        }

        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="badregion").exists())
        self.assertContains(resp, "Niepoprawne dane", status_code=200)

    def test_signup_dob_in_future_rejected(self):
        future_date = (timezone.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "qwertyuiop",   
            "region": "PM",
            "date_of_birth": future_date,
        }
        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="futuredob").exists())
        self.assertContains(resp, "Niepoprawne dane", status_code=200)

    def test_signup_dob_under_13_rejected(self):
        too_young = (timezone.now().date() - relativedelta(years=13) + timedelta(days=1)).strftime("%Y-%m-%d")

        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test123456",
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "qwertyuiop",   
            "region": "PM",
            "date_of_birth": too_young,
        }

        resp = self.client.post("/signup/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="tooyoung").exists())
        self.assertContains(resp, "Niepoprawne dane", status_code=200)


    def test_signup_email_case_insensitive_unique(self):
        User.objects.create_user(
            username="test123456",
            email="tEsT@miko.com",
            password="qwertyuiop",
            date_of_birth=timezone.now().date(),
            region="MZ",
        )
        data = {
            "first_name": "Name",
            "last_name": "lastname",
            "username": "test1234567", # Unique username so email message triggers
            "email": "test@miko.com",
            "password":        "qwertyuiop",
            "confirmPassword": "qwertyuiop",   
            "region": "PM",
            "date_of_birth": '2002-05-10',
        }
        resp = self.client.post("/signup/", data)
        # self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Konto z takim adresem e-mail już istnieje.")

    def test_signin_already_authenticated_get_403(self):
        self.client.login(username="u1", password=self.password)
        resp = self.client.get("/signin/")
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, f"Jesteś zalogowany jako {self.user.username}", status_code=403)

    def test_signout_redirects_home(self):
        self.client.login(username="u1", password=self.password)
        resp = self.client.get("/signout/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/")

    def test_profile_requires_login(self):
        self.client.logout()
        resp = self.client.get("/profile/")
        self.assertEqual(resp.status_code, 302)

    def test_profile_post_no_changes_message(self):
        self.client.login(username="u1", password=self.password)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "region": self.user.region,
            "date_of_birth": str(self.user.date_of_birth),
        }
        resp = self.client.post("/profile/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Niepoprawne dane. Sprawdź formularz.")  

    def test_profile_post_invalid_dob_rejected(self):
        self.client.login(username="u1", password=self.password)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "region": self.user.region,
            "date_of_birth": "invalid-date",
        }
        resp = self.client.post("/profile/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Niepoprawne dane. Sprawdź formularz.")

    def test_profile_post_valid_changes_persisted(self):
        self.client.login(username="u1", password=self.password)
        data = {
            "first_name": "NoweImie",
            "last_name": "NoweNazwisko",
            "region": "PM",
            "date_of_birth": "2001-01-01",
        }
        resp = self.client.post("/profile/", data)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "NoweImie")
        self.assertEqual(self.user.last_name, "NoweNazwisko")
        self.assertEqual(self.user.region, "PM")
        self.assertEqual(str(self.user.date_of_birth), "2001-01-01")
        self.assertContains(resp, "Zmiany zostały zapisane")

    def test_profile_post_invalid_region_rejected(self):
        self.client.login(username="u1", password=self.password)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "region": "XX",
            "date_of_birth": str(self.user.date_of_birth),
        }
        resp = self.client.post("/profile/", data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Niepoprawne dane. Sprawdź formularz.")

    def test_change_password_requires_login(self):
        self.client.logout()
        resp = self.client.post("/changepassword/", {
            "old_password": self.password,   # Dosesn't matter because user is expected to be logged off
            "new_password1": "NewPass!234",
            "new_password2": "NewPass!234",
        })
        self.assertEqual(resp.status_code, 302)

    def test_change_password_wrong_old_password_message(self):
        self.client.login(username="u1", password=self.password)
        resp = self.client.post("/changepassword/", {
            "old_password": "wrong-old",
            "new_password1": "NewPass!234",
            "new_password2": "NewPass!234",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Niepoprawne stare hasło")

    def test_change_password_mismatch_new_passwords_message(self):
        self.client.login(username="u1", password=self.password)
        resp = self.client.post("/changepassword/", {
            "old_password": self.password,
            "new_password1": "NewPass!234",
            "new_password2": "NewPass!999",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Hasła nie są takie same")

    def test_change_password_success_changes_password(self):
        self.client.login(username="u1", password=self.password)
        resp = self.client.post("/changepassword/", {
            "old_password": self.password,
            "new_password1": 'NewPass!234',
            "new_password2": 'NewPass!234',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Hasło zostało zmienione")
        self.client.logout()
        self.assertFalse(self.client.login(username="u1", password=self.password))
        self.assertTrue(self.client.login(username="u1", password='NewPass!234'))


class FormsTests(TestCase):
    def test_user_creation_form_password_mismatch(self):
        form = UserCreationForm(data={
            "username": "formuser",
            "email": "formuser@example.com",
            "password": "Abcdef!2345",
            "password_confirmation": "Different!2345",
            "date_of_birth": "2000-01-01",
            "region": "PM",
        })
        self.assertFalse(form.is_valid()) # bug TODO: form should verify password match 


    def test_user_creation_form_missing_fields(self):
        form = UserCreationForm(data={
            "username": "formuser2",
            "email": "",
            "password": "Abcdef!2345",
            "password_confirmation": "Abcdef!2345",
            "date_of_birth": None,
            "region": None,
        })
        self.assertFalse(form.is_valid())


class SecurityTests(TestCase):
    def test_signup_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        data = {
            "first_name": "CSRF",
            "last_name": "Test",
            "username": "csrfuser",
            "email": "csrfuser@example.com",
            "password": "Abcdef!2345",
            "confirmPassword": "Abcdef!2345",
            "region": "PM",
            "date_of_birth": "2000-01-01",
        }
        resp = client.post("/signup/", data)
        self.assertEqual(resp.status_code, 403)