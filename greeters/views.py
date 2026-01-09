import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from PIL import Image

from core.models import Email_Mailjet
from greeters.forms import GreeterCombinedForm
from greeters.models import Greeter 
from users.models import CustomUser
from users.tasks import reset_password
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.db import transaction

User=get_user_model()

class GreeterCreateView(CreateView):
    model = Greeter
    form_class = GreeterCombinedForm
    template_name = 'greeters/greeter_form.html'
    success_url = reverse_lazy('greeter_list')

    def form_valid(self, form):
        # On utilise une transaction pour s'assurer que si la création du 
        # Greeter échoue, l'utilisateur n'est pas créé (atomicité).
        with transaction.atomic():
            # 1. Création du CustomUser
            # On extrait les données spécifiques à l'utilisateur du formulaire
            user_data = {
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'cellphone': form.cleaned_data['cellphone'],
                'lang_com': form.cleaned_data['lang_com'],
            }
            # Note : Pensez à gérer le mot de passe ici si nécessaire
            user = User.objects.create_user(**user_data)

            # 2. Création du Greeter
            self.object = form.save(commit=False)
            self.object.user = user  # On lie le Greeter à l'utilisateur créé
            self.object.save()
            
            # Important pour les relations ManyToMany (ex: langues_parlées)
            form.save_m2m()

        return super().form_valid(form)