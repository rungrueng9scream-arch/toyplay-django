from django.contrib.auth.hashers import make_password
from django.db import migrations

ADMIN_USERNAME = "boss"
ADMIN_PASSWORD = "1"
ADMIN_EMAIL = "boss@toyplay.local"


def create_default_admin(apps, schema_editor):
    User = apps.get_model("auth", "User")
    user, created = User.objects.get_or_create(
        username=ADMIN_USERNAME,
        defaults={
            "email": ADMIN_EMAIL,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    user.email = user.email or ADMIN_EMAIL
    user.password = make_password(ADMIN_PASSWORD)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("myapp", "0008_seed_categories_coupons"),
    ]

    operations = [
        migrations.RunPython(create_default_admin, migrations.RunPython.noop),
    ]
