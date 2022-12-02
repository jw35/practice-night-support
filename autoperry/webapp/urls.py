from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r"dashboard/", views.dashboard, name="dashboard"),
    path(r"accounts/", include("django.contrib.auth.urls")),
    path(r"register/", views.register, name="register"),
]
