from django.contrib import admin
from django.urls import path
from greeters import views as greeters_views

urlpatterns = [
    path ('greeter/create/', greeters_views.GreeterCreateView.as_view(), name='greeter_create'),
    #path ('greeter/list/', greeters_views.GreeterListView.as_view(), name='greeters_list'),
   # path ('greeter/<int:pk>/update/', greeters_views.GreeterUpdateView.as_view(), name='greeter_update'),
]