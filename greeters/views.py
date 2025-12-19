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
from greeters.forms import GreeterCreationForm, CustomUserCreationForm  
from greeters.models import Greeter 
from users.models import CustomUser
from users.tasks import reset_password
# Create your views here.

User=get_user_model()

class CreationGreeter(View):
   
   def get(self, request, *args, **kwargs):
        user_form = CustomUserCreationForm()
        greeter_form =GreeterCreationForm()
        context =  {'user_form': user_form,'greeter_form':greeter_form,'title': _("Création d'un Greeter")}
        return render(request, 'greeters/greeter_form.html', context)

   def post(self, request, *args, **kwarg):

        if request.method =='POST':
            user_form = CustomUserCreationForm(request.POST)
            greeter_form = GreeterCreationForm(request.POST, request.FILES)
            if user_form.is_valid() and greeter_form.is_valid():
                user= user_form.save()
                groupe=Group.objects.get(name='Greeter')
                user.groups.add(groupe)                
                greeter=greeter_form.save(commit=False)
                greeter.user =user
                greeter.save()
                img_path=os.path.join(settings.MEDIA_ROOT, str(greeter.photo.name))
                img = Image.open(img_path)
                img.thumbnail ((200,200))
                img.save(img_path)
                post_save.send(sender=CustomUser, instance=user, created=True, request=request)
                messages.success(request, _("Le Greeter {} a été créé. Un email lui a été envoyé pour définir son mot de passe.").format(user.email))
                return redirect('greeter_list')
        context =  {'user_form': user_form,'greeter_form':greeter_form,'title': _("Création d'un Greeter")}
        return render(request, 'greeters/greeter_form.html', context)