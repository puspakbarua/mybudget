import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def rename_profile_table(apps, schema_editor):
    profile_model = apps.get_model("profile", "UserProfile")
    table_names = schema_editor.connection.introspection.table_names()
    old_table = "accounts_userprofile"
    new_table = profile_model._meta.db_table

    if old_table in table_names and new_table not in table_names:
        schema_editor.alter_db_table(profile_model, old_table, new_table)
    elif new_table not in table_names:
        schema_editor.create_model(profile_model)


def reverse_rename_profile_table(apps, schema_editor):
    profile_model = apps.get_model("profile", "UserProfile")
    table_names = schema_editor.connection.introspection.table_names()
    old_table = "accounts_userprofile"
    new_table = profile_model._meta.db_table

    if new_table in table_names and old_table not in table_names:
        schema_editor.alter_db_table(profile_model, new_table, old_table)


def rename_profile_content_type(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    alias = schema_editor.connection.alias
    content_types = ContentType.objects.using(alias)
    content_types.filter(app_label="accounts", model="userprofile").update(
        app_label="profile"
    )


def reverse_rename_profile_content_type(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    alias = schema_editor.connection.alias
    ContentType.objects.using(alias).filter(
        app_label="profile", model="userprofile"
    ).update(app_label="accounts")


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="UserProfile",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("email_verified", models.BooleanField(default=False)),
                        (
                            "email_verification_token",
                            models.CharField(
                                blank=True, max_length=255, null=True, unique=True
                            ),
                        ),
                        (
                            "email_verification_token_expires_at",
                            models.DateTimeField(blank=True, null=True),
                        ),
                        (
                            "password_reset_token",
                            models.CharField(
                                blank=True, max_length=255, null=True, unique=True
                            ),
                        ),
                        (
                            "password_reset_token_expires_at",
                            models.DateTimeField(blank=True, null=True),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "user",
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="profile",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "User Profile",
                        "verbose_name_plural": "User Profiles",
                    },
                ),
            ],
        ),
        migrations.RunPython(rename_profile_table, reverse_rename_profile_table),
        migrations.RunPython(
            rename_profile_content_type, reverse_rename_profile_content_type
        ),
    ]
