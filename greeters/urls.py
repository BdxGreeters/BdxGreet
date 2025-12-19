from django.contrib import admin
from django.urls import path
from greeters import views as greeters_views

urlpatterns = [
    path ('greeter/create/', greeters_views.CreationGreeter.as_view(), name='greeter_create'),
]