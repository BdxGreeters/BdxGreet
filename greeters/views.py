from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from .forms import GreeterCombinedForm
from .models import Greeter
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from core.tasks import envoyer_email_creation_utilisateur, resize_image_task

User = get_user_model()


class GreeterCreateView(LoginRequiredMixin, CreateView):
    model = Greeter
    form_class = GreeterCombinedForm
    template_name = 'greeters/greeter_form.html'
    success_url = reverse_lazy('greeters_list')

    def get_form_kwargs(self):
        """Passe l'utilisateur actuel au formulaire"""
        kwargs = super().get_form_kwargs()
        kwargs['admin_user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Récupération des infos de l'admin connecté
        admin = self.request.user
        
        # Pré-remplissage automatique si l'admin a ces champs
        if hasattr(admin, 'cluster') and admin.code_cluster:
            initial['cluster'] = admin.code_cluster
        if hasattr(admin, 'destination') and admin.code_dest:
            initial['destination'] = admin.code_dest
            
        return initial

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # 1. Création de l'utilisateur (CustomUser)
                user_data = {
                    'email': form.cleaned_data['email'],
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'cellphone': form.cleaned_data['cellphone'],
                    'lang_com': form.cleaned_data['lang_com'],
                    'code_cluster': form.cleaned_data['cluster'],
                    'code_dest': form.cleaned_data['destination'],
                }
                new_user = User.objects.create_user(**user_data)

                # 2. Création du Greeter (lié au nouvel user)
                greeter = form.save(commit=False)
                greeter.user = new_user
                greeter.save()
            
                # Sauvegarde des relations ManyToMany (langues, centres d'intérêt, etc.)
                form.save_m2m()

                # 3. Lancement de la tâche Celery pour la photo
                if greeter.photo: 
                    transaction.on_commit(lambda: resize_image_task.delay(
                        app_label='greeters', model_name='Greeter', object_id=greeter.id, field_name ='photo', width=200, height=200))

                # 4. Envoi du courriel pour la création du mot de passe 
                transaction.on_commit(
                    lambda u_id=new_user.id: envoyer_email_creation_utilisateur(u_id, self.request)
                )

                # 5. Affecter le groupe "Greeter" à l'utilisateur
                greeter_group, created = Group.objects.get_or_create(name='Greeter')
                new_user.groups.add(greeter_group)

        except IntegrityError:
            form.add_error('email', _("Cette adresse email est déjà utilisée par un autre compte."))
            return self.form_invalid(form)
        
        return super().form_valid(form)
###################################################################################################
# Mise à jour d'un Greeter existant avec son utilisateur lié

class GreeterUpdateView(LoginRequiredMixin, UpdateView):

    model = Greeter
    form_class = GreeterCombinedForm
    template_name = 'greeters/greeter_form.html'
    success_url = reverse_lazy('greeters:list')

    def get_initial(self):
        """Pré-remplit les champs de CustomUser dans le formulaire"""
        initial = super().get_initial()
        user = self.object.user
        initial.update({
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'cellphone': user.cellphone,
            'lang_com': user.lang_com,
            'code_cluster': user.cluster,
            'code_dest': user.destination,
        })
        return initial

    def form_valid(self, form):
        with transaction.atomic():
            greeter = form.save(commit=False)
            user = greeter.user
            
            # Mise à jour des données utilisateur
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.cellphone = form.cleaned_data['cellphone']
            user.lang_com = form.cleaned_data['lang_com']
            user.code_cluster = form.cleaned_data['cluster']
            user.code_dest = form.cleaned_data['destination']
            user.save()

            # Mise à jour du Greeter
            greeter.save()
            form.save_m2m()

            # Celery si une nouvelle photo est soumise
            if 'photo' in form.changed_data and greeter.photo:
                from core.tasks import resize_image_task as resize_greeter_photo
                transaction.on_commit(lambda: resize_greeter_photo.delay(
                    app_label='greeters', model_name='Greeter', object_id=greeter.id, image_field_name='photo', size=(200, 200)))


        return super().form_valid(form)
    
###################################################################################################
# Vue Liste des greeters
