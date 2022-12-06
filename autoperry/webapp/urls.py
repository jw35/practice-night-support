from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r"accounts/", include("django.contrib.auth.urls")),
    path(r"register/", views.register, name="register"),
    path(r"events/", views.events, name="events"),
    path(r"my-events/", views.my_events, name="my-events"),
    path(r"create-event/", views.create_event, name="create-event")
]
