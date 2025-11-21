from django.contrib import admin
from django.urls import path

from cluster import views as cluster_views

urlpatterns = [
    path ('cluster/create/', cluster_views.ClusterCreateView.as_view(), name='cluster_create'),
    path ('cluster/list/', cluster_views.ClusterListView.as_view(), name='clusters_list'),
    path('cluster/<int:pk>/', cluster_views.ClusterDetailView.as_view(), name='cluster_detail'),
    path('cluster/<int:pk>/update/', cluster_views.ClusterUpdateView.as_view(), name='cluster_update'),
]

