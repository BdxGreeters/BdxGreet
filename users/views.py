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


from core.models import Email_Mailjet
from users.forms import  UserCreationForm, UserUpdateForm
from users.models import CustomUser
from users.tasks import reset_password


class UserCreateView(View):
    def get(self, request, *args, **kwargs):
        form = UserCreationForm()
        context = {'form': form, 'title':_("Créer un utilisateur")}
        return render(request, 'users/user_form.html', context)

    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            domain = get_current_site(request).domain
            code_email="SETPW" # code_email reset password
            id_template_mailjet= Email_Mailjet.objects.get(code_email=code_email, lang_email=settings.LANGUAGE_CODE).id_mailjet_email
            reset_password (user.id,domain, id_template_mailjet)
            messages.success(request, _("L'utilisateur {} a été créé. Un email lui a été envoyé pour définir son mot de passe.").format(user.email))
            return redirect('user_list')
        context = {'form': form, 'title':_("Créer un utilisateur")}
        return render(request, 'users/user_form.html', context)

class UserUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)
        form = UserUpdateForm(instance=user)
        context = {'form': form, 'title':_("Modifier {}".format(user.email))}
        return render(request, 'users/user_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'utilisateur {} a été mis à jour.").format(user.email))
            return redirect('user_list')
        context = {'form': form, 'title':_("Modifier {}".format(user.email))}
        return render(request, 'users/user_form.html', context)





class UserListView(View):
    User = get_user_model()
    def get(self, request, *args, **kwargs):
        users = CustomUser.objects.exclude(is_superuser=True).exclude(groups__name='Greeter').order_by('id')
        return render(request, 'users/user_list.html', {'users': users})





def custom_password_reset (request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email=form.cleaned_data['email']
            User=get_user_model()
            users=User.objects.filter(email=email)
            if users.exists():
                user = User.objects.get(email=email)
                domain = get_current_site(request).domain
                code_email="RESPW" # code_email reset password
                id_template_mailjet= Email_Mailjet.objects.get(code_email=code_email, lang_email=user.lang_com).id_mailjet_email
                reset_password (user.id,domain, id_template_mailjet)
                return redirect('password_reset_done')
            else :
                messages.warning (request, _("L'adresse courriel {} n'existe pas dans la base de gestion").format(email))
                form = PasswordResetForm()
                return render(request, "users/password_reset.html", {"form": form})            
    else:
        form = PasswordResetForm()
        return render(request, "users/password_reset.html", {"form": form})
    
