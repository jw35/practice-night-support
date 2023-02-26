from django.contrib import admin
from django.utils import timezone

from webapp.models import Event, Volunteer


class CancelledListFilter(admin.SimpleListFilter):

    """
    SimpleListFilter for 'cancelled' which is a boolean
    recorded as a datetime'
    """

    title = 'cancelled?'
    parameter_name = 'cancelled'

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


class PastListFilter(admin.SimpleListFilter):

    """
    SimpleListFilter for whether the event had happened or not,
    based on start datetime
    """

    title = 'past?'
    parameter_name = 'start'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):

        now = timezone.now()

        if self.value() == 'yes':
            return queryset.filter(**{f'{self.parameter_name}__lt': now})

        if self.value() == 'no':
            return queryset.filter(**{f'{self.parameter_name}__gte': now})



class HelpersInline(admin.TabularInline):
    model = Event.helpers.through
    fields = [
        "person",
        "created",
        "withdrawn",
        "declined",
        "current"
    ]
    readonly_fields = [
        "person",
        "created",
        "current"
    ]
    verbose_name = 'events helped'
    extra = 0
    show_change_link = True
    classes = ( "collapse", )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'start'
    fields = [
        ('start', 'end'),
        ('location', 'helpers_required'),
        'owner',
        'created',
        ('owner_reminded', 'cancelled'),
        ('past', 'helpers_needed'),
        'contact_address',
        'notes',
        ]
    inlines = [
        HelpersInline,
    ]
    list_display = [
        'short_when',
        'location',
        'past',
        'is_cancelled',
        'helpers_required',
        'n_helpers_available',
        'helpers_needed']
    list_filter = [
         PastListFilter,
         CancelledListFilter,
        'location',
        'owner',
        'helpers'
    ]
    ordering = [
        '-start'
    ]
    readonly_fields = [
        'created',
        'past',
        'helpers_needed'
    ]
    search_fields = [
        'location',
        'owner__first_name',
        'owner__last_name',
        'helpers__first_name',
        'helpers__last_name'
    ]
    search_help_text = "Search on location, or owner or helper name"
    view_on_site = True

