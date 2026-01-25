from django.contrib import admin
from django.urls import path
from destination import views as destination_views
from destination.views import get_parent_destination_info

urlpatterns = [
    path ('destination/create/', destination_views.DestinationCreateView.as_view(), name='destination_create'),
    path ('destination/list/', destination_views.DestinationListView.as_view(), name='destinations_list'),
    path('destination/<int:pk>/', destination_views.DestinationDetailView.as_view(), name='destination_detail'),
    path('destination/<int:pk>/update/', destination_views.DestinationUpdateView.as_view(), name='destination_update'),
    path('destination/<int:pk>/fluxupdate/', destination_views.DestinationFluxUpdateView.as_view(), name='destination_flux_update'),
    path('destination/<int:pk>/updatedata/', destination_views.DestinationDataUpdateView.as_view(), name='destination_data_update'), 
    path('ajax/filter-users/', destination_views.AjaxFilterUsersView.as_view(), name='ajax_filter_users'),
    path('api/get-parent-info/', get_parent_destination_info, name='get_parent_info'),
    path('destination/create_related_data/<int:destination_id>/', destination_views.CreateRelatedDataModelsView.as_view(), name='create_related_data'),
    path('destination/create_related_flux/<int:destination_id>/', destination_views.CreateRelatedFluxModelsView.as_view(), name='create_related_flux'),
]