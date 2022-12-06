from django.shortcuts import redirect,  render
from django.contrib.auth import login
from django.urls import reverse
from webapp.forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F

from datetime import datetime

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
    if 'all' in request.GET:
        event_list = Event.objects.all()
        heading = "All events (future and past)"
        if 'past' not in request.GET:
            event_list = event_list.filter(start__gte=datetime.now())
            heading = "All future events"
    else:
        event_list = Event.objects.annotate(num_volounteres=Count('volunteer')).filter(helpers_required__gt=F("num_volounteres"))    
        heading = "Future events needing volounteres"
    return render(request, "events.html",
        context={'events': event_list, 'heading': heading})

@login_required()
def my_events(request):
    return render(request, "my-events.html")

@login_required()
def create_event(request):
    return render(request, "create-event.html")