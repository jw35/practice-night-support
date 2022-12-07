from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login
from django.urls import reverse
from webapp.forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.utils import timezone

from webapp.models import Event

# Create your views here.

from django.http import HttpResponse


def index(request):
    return render(request, "index.html")

def dashboard(request):
    return render(request, "users/dashboard.html")

def register(request):
    if request.method == "GET":
        return render(
            request, "registration/register.html",
            {"form": CustomUserCreationForm}
        )
    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("index"))

def events(request):
    event_list = Event.objects.all().annotate(helpers_available=Count('volunteer'))
    if 'all' in request.GET:
        heading = "All events"
        if 'past' not in request.GET:
            event_list = event_list.filter(start__gte=timezone.now())
            heading = "All future events"
    else:
        event_list = event_list.filter(start__gte=timezone.now()).filter(helpers_required__gt=F("helpers_available"))
        heading = "Events needing helpers"
    return render(request, "events.html",
        context={'events': event_list, 'heading': heading})

@login_required
def volunteer(request, event_id):
    pass

def event_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    user = request.user
    print(user.get_username())

    is_owner = user.is_authenticated and user.get_username() == event.owner.get_username()

    is_helper = False
    if user.is_authenticated:
        for helper in event.helpers.all():
            print(helper.get_username(), user.get_username())
            if helper.get_username() == user.get_username():
                print("Setting is_helprt to True")
                is_helper = True
                print(is_helper)
                break

    print(is_helper)

    return render(request, "event.html",
        context={'event': event,
                 'is_owner': is_owner,
                 'is_helper': is_helper
                })

@login_required()
def my_events(request):
    return render(request, "my-events.html")

@login_required()
def create_event(request):
    return render(request, "create-event.html")