from django.contrib import admin
from django.urls import path
from greeters import views as greeters_views

urlpatterns = [
    path ('greeter/create/', greeters_views.GreeterCreateView.as_view(), name='greeter_create'),
    path ('greeter/list/', greeters_views.GreeterListView.as_view(), name='greeter_list'),
    path ('greeter/<int:pk>/update/', greeters_views.GreeterUpdateView.as_view(), name='greeter_update'),
    path ('greeter/<int:pk>/', greeters_views.GreeterDetailView.as_view(), name='greeter_detail'),
    path('api/get-cluster-data/', greeters_views.get_cluster_dest_data, name='get_cluster_dest_data'),
]
