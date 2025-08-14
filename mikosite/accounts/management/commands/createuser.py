import getpass
from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from ...models import REGION_CHOICES 
from ...forms import UserCreationForm  # Import your form
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a new superuser in terminal.'

    def add_arguments(self, parser):
        parser.add_argument('--username', help="The new superuser's username.")
        parser.add_argument('--email', help="The new superuser's email.")
        parser.add_argument('--date_of_birth', help="The new superuser's date of birth (YYYY-MM-DD).")
        parser.add_argument('--region', help="The new superuser's region code.")
        parser.add_argument('--no-input', '--noinput', action='store_true', help='Do not prompt for input.')

    def handle(self, *args, **options):
        # If --no-input is used, all fields must be provided
        if options['no_input']:
            if not all(options[key] for key in ['username', 'email', 'date_of_birth', 'region']):
                raise CommandError("When using --no-input, you must provide --username, --email, --date_of_birth, and --region.")
        
            username = options['username']
            email = options['email']
            date_of_birth_str = options['date_of_birth']
            region = options['region']
            password = None 
        else:
            #  Interactive Mode
            username = options['username']
            email = options['email']
            date_of_birth_str = options['date_of_birth']
            region = options['region']
            password = None

            # username
            if not username:
                while True:
                    username_input = input("Username: ")
                    if not username_input:
                        self.stderr.write("Error: Username cannot be blank.")
                        continue
                    if User.objects.filter(username=username_input).exists():
                        self.stderr.write("Error: That username is already taken.")
                        continue
                    username = username_input
                    break

            # email
            if not email:
                while True:
                    email_input = input("Email: ")
                    if not email_input:
                        self.stderr.write("Error: Email cannot be blank.")
                        continue
                    email = email_input
                    break
            
            # Date of Birth
            if not date_of_birth_str:
                while True:
                    dob_input = input("Date of Birth (YYYY-MM-DD): ")
                    if not dob_input:
                         self.stderr.write("Error: Date of birth cannot be blank.")
                         continue
                    try:
                        datetime.strptime(dob_input, '%Y-%m-%d').date()
                        date_of_birth_str = dob_input
                        break
                    except ValueError:
                        self.stderr.write("Error: Invalid date format. Please use YYYY-MM-DD.")

            # region
            if not region:
                self.stdout.write("Available Regions:")
                for code, name in REGION_CHOICES:
                    self.stdout.write(f"  {code}: {name}")
                
                valid_regions = [r[0] for r in REGION_CHOICES]
                while True:
                    region_input = input("Region Code: ").upper()
                    if not region_input:
                        self.stderr.write("Error: Region cannot be blank.")
                        continue
                    if region_input not in valid_regions:
                        self.stderr.write("Error: Invalid region code. Please choose from the list above.")
                        continue
                    region = region_input
                    break
        
        # Password 
        while True:
            password = getpass.getpass()
            password2 = getpass.getpass('Password (again): ')
            if password != password2:
                self.stderr.write("Error: Your passwords didn't match.")
                continue
            if password.strip() == '':
                self.stderr.write("Error: Blank passwords aren't allowed.")
                continue
            break

        form_data = {
            'username': username,
            'email': email,
            'password': password,
            'password_confirmation': password,
            'date_of_birth': date_of_birth_str,
            'region': region,
        }
        
        form = UserCreationForm(form_data)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Check if username already exists (additional check)
            if User.objects.filter(username=cleaned_data['username']).exists():
                raise CommandError(f'User with username "{cleaned_data["username"]}" already exists.')
            
            # Create the superuser using cleaned data
            try:
                user = User.objects.create_user(
                    username=cleaned_data['username'],
                    email=cleaned_data['email'],
                    password=cleaned_data['password'],
                    date_of_birth=cleaned_data['date_of_birth'],
                    region=cleaned_data['region']
                )
                self.stdout.write(self.style.SUCCESS(f'Regular user "{user.username}" created successfully.'))
            except Exception as e:
                raise CommandError(f'Error creating regular user: {e}')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f'{field}: {error}')
            
            for error in form.non_field_errors():
                error_messages.append(f'General error: {error}')
            
            raise CommandError('\n'.join(error_messages))