from django.contrib import admin
from django.urls import path

from core import views as core_views
from core.views import get_languages

urlpatterns = [
    # URLs de notre application
    path('core/email_mailjet/create/', core_views.Email_MailjetCreateView.as_view(), name='create_email_mailjet'),
    path('core/email_mailjet/list/', core_views.Email_MailjetListView.as_view(), name='email_mailjet_list'),
    path('core/email_mailjet/update/<int:pk>/', core_views.Email_MailjetUpdateView.as_view(), name='email_mailjet_update'),
    path('core/langue_deepl/create/',core_views.LangueDeepLCreateView.as_view(), name='create_langue_deepl'),
    path('core/langue_deepl/list/',core_views.LangueDeeplListView.as_view(), name='langue_deepl_list'),
    path('core/langue_deepl/update/<int:pk>/',core_views.LangueDeepLUpdateView.as_view(), name='langue_deepl_update'),
    path('core/interest_center/create/',core_views.InterestCenterCreationView.as_view(), name='create_interest_center'),
    path('core/interest_center/list/',core_views.InterestCenterListView.as_view(), name='interest_center_list'),
    path('core/interest_center/update/<int:pk>/',core_views.InterestCenterUpdateView.as_view(), name='interest_center_update'),
    path('core/no_show/create/',core_views.No_showCreationView.as_view(), name='create_no_show'),
    path('core/no_show/list/',core_views.No_showListView.as_view(), name='no_show_list'),
    path('core/no_show/update/<int:pk>/',core_views.No_showUpdateView.as_view(), name='no_show_update'),
    path('core/beneficiaire/create/',core_views.BeneficiaireCreationView.as_view(), name='create_beneficiaire'),
    path('core/beneficiaire/list/',core_views.BeneficiaireListView.as_view(), name='beneficiaire_list'),
    path('core/beneficiaire/update/<int:pk>/',core_views.BeneficiaireUpdateView.as_view(), name='beneficiaire_update'),
    path('core/periode/create/',core_views.PeriodeCreationView.as_view(), name='create_periode'),
    path('core/periode/list/',core_views.PeriodeListView.as_view(), name='periode_list'),
    path('core/periode/update/<int:pk>/',core_views.PeriodeUpdateView.as_view(), name='periode_update'),
    path('core/tranche_age/create/',core_views.TrancheAgeCreationView.as_view(), name='create_tranche_age'),
    path('core/tranche_age/list/',core_views.TrancheAgeListView.as_view(), name='tranche_age_list'),
    path('core/tranche_age/update/<int:pk>/',core_views.TrancheAgeUpdateView.as_view(), name='tranche_age_update'),
    path('core/types_handicap/create/',core_views.Types_handicapCreationView.as_view(), name='create_types_handicap'),
    path('core/types_handicap/list/',core_views.Types_handicapListView.as_view(), name='types_handicap_list'),
    path('core/types_handicap/update/<int:pk>/',core_views.Types_handicapUpdateView.as_view(), name='types_handicap_update'),
    path('core/users_create/',core_views.CreateUserView.as_view(), name='create_user'),
    path('core/get-languages/', get_languages, name='get-languages'),
    path('core/get-users/', core_views.get_users_json, name='get-users'),

]