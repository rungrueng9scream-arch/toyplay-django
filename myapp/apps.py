import os

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_superuser_from_env(sender, **kwargs):
    """Sync a superuser with the DJANGO_SUPERUSER_* env vars on every migrate/start.

    - If the user does not exist: create it as an active superuser + staff.
    - If it already exists: reset the password and ensure active superuser + staff.
    """
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

    if not username or not password:
        return

    from django.contrib.auth import get_user_model

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email},
    )
    if email:
        user.email = email
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save()


class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        post_migrate.connect(sync_superuser_from_env, sender=self)
