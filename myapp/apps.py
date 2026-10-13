from django.apps import AppConfig
from django.db.models.signals import post_migrate
import os


def create_render_superuser(sender, **kwargs):
    """Create a superuser automatically during migrate when env vars are set."""
    from django.contrib.auth.models import User

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if not username or not password:
        return

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)


class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        post_migrate.connect(create_render_superuser, sender=self)