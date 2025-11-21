
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import include, path

from users import views as account_views

urlpatterns = [
    # URLs d'authentification personnalisées
    path('', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name ='logout'),
    path('password_reset/', account_views.custom_password_reset, name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='users/password_set_form.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),

    # URLs de votre application
    path('users/create/', account_views.UserCreateView.as_view(), name='create_user'),
    path('greeter/<int:pk>/update/', account_views.GreeterUpdateGreeter.as_view(), name='greeter_update'),
    path('users/<int:pk>/update/', account_views.UserUpdateView.as_view(), name='user_update'),
    path('greeter/create/', account_views.CreationGreeter.as_view(), name='create_greeter'),
    path('users/', account_views.UserListView.as_view(), name='user_list'),
    path('greeters/', account_views.GreeterListView.as_view(), name='greeter_list'),
]
