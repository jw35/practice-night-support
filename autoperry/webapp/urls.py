from django.urls import include, path
from django.views.generic import TemplateView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(r'favicon.ico', RedirectView.as_view(url=staticfiles_storage.url("webapp/favicon.ico"))),
    path(r'privacy', TemplateView.as_view(template_name="webapp/privacy.html"), name='privacy'),
    path(r'help/about', TemplateView.as_view(template_name="webapp/about.html"), name='about'),
    path(r'help/organisers', TemplateView.as_view(template_name="webapp/organisers.html"), name='guidelines-organisers'),
    path(r'help/helpers', TemplateView.as_view(template_name="webapp/helpers.html"), name='guidelines-helpers'),
    path(r"accounts/password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(r"accounts/", include("django.contrib.auth.urls")),
    path(r"account", views.account, name="account"),
    path(r"account/create", views.account_create, name="account-create"),
    path(r"account/confirm/<uidb64>/<token>", views.account_confirm, name="account-confirm"),
    path(r"account/resend", views.account_resend, name="account-resend"),
    path(r"account/edit", views.account_edit, name="account-edit"),
    path(r"account/cancel", views.account_cancel, name="account-cancel"),
    path(r"events", views.events, name="events"),
    path(r"event/create", views.event_create, name="event-create"),
    path(r"event/<int:event_id>", views.event_details, name="event-details"),
    path(r"event/<int:event_id>/cancel", views.event_cancel, name="event-cancel"),
    path(r"event/<int:event_id>/edit", views.event_edit, name="event-edit"),
    path(r"event/<int:event_id>/clone", views.event_clone, name="event-clone"),
    path(r"event/<int:event_id>/volunteer", views.volunteer, name="volunteer"),
    path(r"event/<int:event_id>/unvolunteer", views.unvolunteer, name="unvolunteer"),
    path(r"event/<int:event_id>/decline/<int:helper_id>", views.decline, name="decline"),
    path(r"admin/send-emails", views.send_emails, name="send-emails"),
    path(r"admin/account-list", views.account_list, name="account-list"),
    path(r"admin/account-approve-list", views.account_approve_list, name="account-approve-list"),
    path(r"admin/account-approve/<int:user_id>", views.account_approve, name="account-approve"),
    path(r"admin/account-toggle/<str:action>/<int:user_id>", views.account_toggle, name="account-toggle"),
]
