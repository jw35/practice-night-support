from django.contrib import admin

from webapp.models import Event, Volunteer

# Register your models here.

class HelpersInline(admin.TabularInline):
    model = Event.helpers.through
    readonly_fields = ['created', 'current']
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = 'start'
    search_fields = ['location', 'owner__first_name', 'owner__last_name',
                     'helpers__first_name', 'helpers__last_name']
    inlines = [
        HelpersInline,
    ]
    fields = ['start', 'end', 'location', 'helpers_required', 'owner', 'created',
              'cancelled', 'past', 'helpers_needed', 'contact_address', 'notes',
              'owner_reminded']
    readonly_fields = ['created', 'past', 'helpers_needed']
    view_on_site = True

