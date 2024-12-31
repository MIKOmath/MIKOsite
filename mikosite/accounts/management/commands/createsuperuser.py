from django.contrib.auth.management.commands import createsuperuser

class Command(createsuperuser.Command):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--name', required=False)
        parser.add_argument('--surname', required=False)

    def handle(self, *args, **options):

        if options.get('interactive'):
            print("Attention! Currently interactive mode is not fully available. \n"
                  "You have to change new superusers name and surname manually in Django Admin panel.")


        user = super().handle(*args, **options)

        return user
