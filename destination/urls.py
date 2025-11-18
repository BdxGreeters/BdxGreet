from django.contrib import admin
from django.urls import path
from destination import views as destination_views

urlpatterns = [
    path ('destination/create/', destination_views.DestinationCreateView.as_view(), name='destination_create'),
    path ('destination/list/', destination_views.DestinationListView.as_view(), name='destinations_list'),
    #path('cluster/<int:pk>/', cluster_views.ClusterDetailView.as_view(), name='cluster_detail'),
    #path('cluster/<int:pk>/update/', cluster_views.ClusterUpdateView.as_view(), name='cluster_update'),
    path('ajax/filter-users/', destination_views.AjaxFilterUsersView.as_view(), name='ajax_filter_users'),
    path('destination/wizard/', destination_views.DestinationCreationWizard.as_view(), name='destination_wizard'),
]