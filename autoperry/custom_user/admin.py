from django.contrib import admin
from django_use_email_as_username.admin import BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User

class CustomBaseUserAdmin(BaseUserAdmin):

	fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "cancelled")}),
    )

admin.site.register(User, CustomBaseUserAdmin)
