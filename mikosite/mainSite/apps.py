from django.apps import AppConfig


class MainsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainSite'

    def ready(self):
        from .models import Tag
        default_tags = ['matematyka', 'informatyka', 'AI', 'fizyka']
        for name in default_tags:
            Tag.objects.get_or_create(name=name)
