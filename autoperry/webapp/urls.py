from django.urls import include, path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r'privacy', TemplateView.as_view(template_name="privacy.html"), name='privacy'),
    path(r'about', TemplateView.as_view(template_name="about.html"), name='about'),
    path(r"accounts/", include("django.contrib.auth.urls")),
    path(r"account/", views.account, name="account"),
    path(r"account/create", views.account_create, name="account-create"),
    path(r"account/edit", views.account_edit, name="account-edit"),
    path(r"account/cancel", views.account_cancel, name="account-cancel"),
    path(r"events/", views.events, name="events"),
    path(r"event/create/", views.event_create, name="event-create"),
    path(r"event/<int:event_id>/", views.event_details, name="event-details"),
    path(r"event/<int:event_id>/cancel", views.event_cancel, name="event-cancel"),
    path(r"event/<int:event_id>/edit", views.event_edit, name="event-edit"),
    path(r"event/<int:event_id>/clone", views.event_clone, name="event-clone"),
    path(r"event/<int:event_id>/volunteer/", views.volunteer, name="volunteer"),
    path(r"event/<int:event_id>/unvolunteer/", views.unvolunteer, name="unvolunteer")
]
