from django.apps import AppConfig


class SignalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seminars'
    def ready(self):
        import seminars.signals
