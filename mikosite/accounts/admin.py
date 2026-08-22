from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "full_name", "is_staff", "is_superuser")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-is_superuser", "-is_staff", "username")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "region", "date_of_birth", "profile_image")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Additional info"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "first_name", "last_name", "region", "date_of_birth", "password1", "password2"),
        }),
    )


# Provider credentials live in settings and tokens are not stored, so only the
# account linkage itself belongs in the admin. The import forces allauth's
# registrations so they can be replaced regardless of app ordering.
from allauth.socialaccount import admin as _socialaccount_admin  # noqa: E402,F401
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken  # noqa: E402
from django.contrib.admin.exceptions import NotRegistered  # noqa: E402

for _model in (SocialAccount, SocialApp, SocialToken):
    try:
        admin.site.unregister(_model)
    except NotRegistered:
        pass


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "uid", "last_login")
    list_filter = ("provider",)
    search_fields = ("user__username", "uid")
