from django.contrib import admin
from django_use_email_as_username.admin import BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User
from webapp.models import Event

class HelpedInLine(admin.TabularInline):
    model = User.events_volunteered.through
    fields = [
        "event",
        "created",
        "withdrawn",
        "declined",
        "current"
    ]
    readonly_fields = [
        "event",
        "created",
        "current"
    ]
    verbose_name = 'events helped'
    extra = 0
    show_change_link = True
    classes = ( "collapse", )

class OwnedInLine(admin.TabularInline):
    fields = [
        "__str__"
    ]
    readonly_fields = [
        "__str__"
    ]
    model = Event
    extra = 0
    show_change_link = True
    classes = ( "collapse", )

class BooleanDateListFilter(admin.SimpleListFilter):

    """
    SimpleListFilter for 'cancelled' which is a boolean
    recorded as a datetime'
    """

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.exclude(**{f'{self.parameter_name}__exact': None})

        if self.value() == 'no':
            return queryset.filter(**{f'{self.parameter_name}__exact': None})


class ValidatedListFilter(BooleanDateListFilter):
    title = 'email validated?'
    parameter_name = 'email_validated'


class ApprovedListFilter(BooleanDateListFilter):
    title = 'approved?'
    parameter_name = 'approved'


class SuspendedListFilter(BooleanDateListFilter):
    title = 'suspended?'
    parameter_name = 'suspended'


class CacelledListFilter(BooleanDateListFilter):
    title = 'canceleld?'
    parameter_name = 'cancelled'


class CustomBaseUserAdmin(BaseUserAdmin):

    fieldsets = (
        (
            None, {
                "fields": (
                    "last_name",
                    "first_name",
                    "email",
                    "phone_number",
                    "tower",
                    ("send_notifications", "send_other"),
                    "volunteer_celebration",
                )
            }
        ),
        (
            "Password", {
                "fields": (
                    "password",
                    "uuid",
                ),
                "classes": (
                    "collapse",
                )
            }
        ),
        (
            "Important dates", {
                "fields": (
                    "date_joined",
                    "last_login",
                    "approved",
                    "email_validated",
                    "reminded_upto",
                    "cancelled",
                    "suspended",
                    "email_blocked"
                )
            }
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": (
                    "collapse",
                )
            },
        ),
    )

    inlines = [
        OwnedInLine,
        HelpedInLine,
    ]

    list_display = [
        "last_name",
        "first_name",
        "email",
        "is_email_validated",
        "is_approved",
        "is_suspended",
        "is_cancelled",
        "is_enabled",
        "n_events_helped",
        "n_events_owned"]

    list_display_links =[
        "last_name",
        "first_name",
        "email",
    ]

    list_filter = [
        ValidatedListFilter,
        ApprovedListFilter,
        SuspendedListFilter,
        CacelledListFilter,
    ]

    ordering = [
        "last_name",
        "first_name",
        "email",
    ]

    search_fields = [
        "last_name",
        "first_name",
        "email",
    ]



admin.site.register(User, CustomBaseUserAdmin)
