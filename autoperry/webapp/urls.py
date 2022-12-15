from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r"accounts/", include("django.contrib.auth.urls")),
    path(r"events/", views.events, name="events"),
    path(r"events/mine/", views.my_events, name="my-events"),
    path(r"event/create/", views.create_event, name="create-event"),
    path(r"event/<int:event_id>/", views.event_details, name="event-details"),
    path(r"event/<int:event_id>/cancel", views.cancel_event, name="cancel-event"),
    path(r"event/<int:event_id>/volunteer/", views.volunteer, name="volunteer"),
    path(r"event/<int:event_id>/unvolunteer/", views.unvolunteer, name="unvolunteer")
]
