from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views import View
from django.shortcuts import render
from django.db import transaction

from cluster.forms import ClusterForm
from cluster.models import (
    Cluster, Experience_Greeter, InterestCenter, 
    Reason_No_Response_Greeter, Reason_No_Response_Visitor, Notoriety
)
from destination.models import Destination
from core.mixins import FormFieldPermissionMixin, RelatedModelsMixin
from core.tasks import envoyer_email_creation_utilisateur

User = get_user_model()

class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='SuperAdmin').exists() 

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour créer un cluster."))
        return redirect('clusters_list')

class ClusterCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, FormFieldPermissionMixin, RelatedModelsMixin, CreateView):
    template_name = 'cluster/cluster_form.html'
    success_url = reverse_lazy('clusters_list')
    form_class = ClusterForm
    permission_groups = ['SuperAdmin']
    target_group_name = 'Admin'
    app_name = 'cluster'
    
    related_fields = {
        'experience_greeter': (Experience_Greeter, 'experience_greeter', 'experience_greeter'),
        'interest_center': (InterestCenter, 'interest_center', 'interest_center'),
        'no_reply_greeter': (Reason_No_Response_Greeter, 'reason_no_reply_greeter', 'reason_no_reply_greeter'),
        'no_reply_visitor': (Reason_No_Response_Visitor, 'reason_no_reply_visitor', 'reason_no_reply_visitor'),
        'notoriety': (Notoriety, 'notoriety', 'notoriety')  
    }

    def form_valid(self, form):
        """
        Point d'entrée principal après validation du formulaire.
        """
        pending_adm_id = self.request.POST.get('pending_adm_id')
        pending_adm_alt_id = self.request.POST.get('pending_adm_alt_id')
        print(f"DEBUG: pending_adm_id={pending_adm_id}, pending_adm_alt_id={pending_adm_alt_id}")
        try:
            with transaction.atomic():
                # 1. Sauvegarde l'instance Cluster
                # Le form.save() gère déjà les admins (admin_cluster / admin_alt_cluster)
                self.object = form.save()
                cluster = self.object

                # 2. Appel du Mixin générique pour les RelatedFields
                self.save_related_data(form)

                # 3. Gestion des utilisateurs AJAX (Pending Admin, Pendig Admin Alt)
                pending_admins = [pending_adm_id, pending_adm_alt_id]
                
                for adm_id in pending_admins:
                    if adm_id:
                        try:
                            # Utilisation de select_for_update pour verrouiller la ligne
                            new_user = User.objects.select_for_update().get(id=adm_id)
                            new_user.code_cluster = cluster
                            new_user.is_active = True
                            
                            admin_group, creted = Group.objects.get_or_create(name='Admin')
                            new_user.groups.add(admin_group)
                            new_user.save()
                            print(f"Utilisateur {new_user.id} lié au cluster {cluster.code_cluster} et activé.")

                            # Appel de la tâche : on passe l'ID pour la sécurité
                            # La transaction.on_commit est gérée à l'intérieur de la fonction
                            envoyer_email_creation_utilisateur(new_user.id, self.request)
                            
                        except User.DoesNotExist:
                            continue
                


                # 4. Mise à jour des permissions de champs (via FormFieldPermissionMixin)
                if hasattr(self, 'update_field_permissions'):
                    self.update_field_permissions(cluster, form)

                # 5. Message de succès et Redirection
                messages.success(self.request, _("Le cluster {} a été créé avec succès.").format(cluster.name_cluster))
                return redirect(self.get_success_url())

        except Exception as e:
            # En cas d'erreur, self.object est réinitialisé pour éviter les crashs de contexte
            self.object = None 
            messages.error(self.request, _("Erreur lors de la création : ") + str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Gestion spécifique en cas d'échec du formulaire.
        """
        pending_adm_id = self.request.POST.get('pending_adm_id')
        pending_adm_alt_id = self.request.POST.get('pending_adm_alt_id')

        if pending_adm_id:
            # Suppression de l'utilisateur orphelin créé via AJAX
            User.objects.filter(id=pending_adm_id, code_cluster__isnull=True).delete()
        if pending_adm_alt_id:
            User.objects.filter(id=pending_adm_alt_id, code_cluster__isnull=True).delete()

        messages.error(self.request, _("Le formulaire n'est pas valide. Veuillez vérifier les champs."))
        return super().form_invalid(form)
###################################################################################################

#Vue Liste des clusters

class AuthorizationListRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.groups.filter(
            name__in=["SuperAdmin", "Admin"]
        ).exists()

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les droits nécessaires pour afficher la liste des clusters.")
        return redirect('login')

class ClusterListView(AuthorizationListRequiredMixin,View):
    
    def get(self, request, *args, **kwargs):
        clusters = Cluster.objects.all().order_by('code_cluster')
        return render(request, 'cluster/clusters_list.html', {'clusters': clusters})   

###################################################################################################
#Vue Détail d'un cluster

class SuperAdminOrAdminRequiredMixin(UserPassesTestMixin):
    

    def test_func(self):
    # Autoriser les SuperAdmin ou les utilisateurs qui sont admin/admin_alt du cluster
        cluster = self.get_object()
        return (
            self.request.user.groups.filter(name = 'SuperAdmin').exists() or
            self.request.user == cluster.admin_cluster or
            self.request.user == cluster.admin_alt_cluster
            )

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour consulter ce cluster."))
        return redirect('clusters_list')

class ClusterDetailView(LoginRequiredMixin, SuperAdminOrAdminRequiredMixin, DetailView):
    model = Cluster
    template_name = 'cluster/cluster_detail.html'  # Template dédié à la consultation
    context_object_name = 'cluster'  # Nom de l'objet dans le contexte

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cluster = self.object
        # Récupérer les destinations associées au cluster
        destinations = Destination.objects.filter(code_cluster=cluster)
        if not destinations.exists():  # Vérifie si la liste est vide
            context['no_destinations'] = True  # Ajoute un indicateur dans le contexte
            context['destinations'] = []  # Passe une liste vide
        else:
            context['destinations'] = destinations
        context['title'] = _("Détail du cluster")
        return context
###################################################################################################
#Vue Modification d'un cluster

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from core.mixins import FormFieldPermissionMixin


from cluster.forms import ClusterForm
from cluster.models import Cluster


class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        cluster = self.get_object()
        return (
            self.request.user.groups.filter(name='SuperAdmin').exists() or
            self.request.user == cluster.admin_cluster or
            self.request.user == cluster.admin_alt_cluster
        )

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour modifier ce cluster."))
        return redirect('clusters_list')

class ClusterUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, FormFieldPermissionMixin, RelatedModelsMixin, UpdateView):
    model = Cluster
    form_class = ClusterForm
    template_name = 'cluster/cluster_form.html'
    success_url = reverse_lazy('clusters_list')
    title = _("Modification du cluster")
    permission_groups = ['SuperAdmin']
    target_group_name = 'Admin'
    app_name = 'cluster'
    
    related_fields = {
        'experience_greeter': (Experience_Greeter, 'experience_greeter', 'experience_greeter'),
        'interest_center': (InterestCenter, 'interest_center', 'interest_center'),
        'no_reply_greeter': (Reason_No_Response_Greeter, 'reason_no_reply_greeter', 'reason_no_reply_greeter'),
        'no_reply_visitor': (Reason_No_Response_Visitor, 'reason_no_reply_visitor', 'reason_no_reply_visitor'),
        'notoriety': (Notoriety, 'notoriety', 'notoriety')  
    }

    def get_initial(self):
        initial = super().get_initial()
        cluster = self.get_object()
        # Pré-remplissage des champs texte (tags) à partir des relations M2M
        for form_field, (model, m2m_field, model_attr) in self.related_fields.items():
            existing_values = getattr(cluster, m2m_field).values_list(model_attr, flat=True)
            initial[form_field] = ', '.join(existing_values)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Gestion des permissions de champs (lecture seule si non SuperAdmin)
        if not self.user_has_any_permission_group(self.request.user):
            permissions = self.get_field_permissions(self.object)
            for field_name, is_editable in permissions.items():
                if not is_editable and field_name in form.fields:
                    form.fields[field_name].disabled = True
        
        # Sécurité : Le code cluster est l'identifiant métier unique, non modifiable
        form.fields['code_cluster'].disabled = True
        return form

    def form_valid(self, form):
        # 1. Vérification de sécurité : Un administrateur principal est-il présent ?
        # On vérifie dans cleaned_data car c'est la valeur que l'utilisateur veut enregistrer
        if not form.cleaned_data.get('admin_cluster'):
            messages.error(self.request, _("Erreur : Un cluster doit obligatoirement avoir un administrateur principal."))
            return self.form_invalid(form)

        # 2. Récupération de l'état avant sauvegarde pour comparaison
        old_instance = self.get_object()
        old_admins = {old_instance.admin_cluster, old_instance.admin_alt_cluster} - {None}

        try:
            with transaction.atomic():
                # 3. Sauvegarde du formulaire (Met à jour self.object)
                # Le save() du ClusterForm lie déjà le code_cluster aux nouveaux admins
                self.object = form.save()
                cluster = self.object

                # 4. Traitement générique des RelatedFields (via le Mixin)
                self.save_related_data(form)

                # 5. Gestion des utilisateurs AJAX (Peding Admin et Pending Admin Alt)
                pending_adm_id = form.cleaned_data.get('pending_adm_id')
                pending_adm_alt_id = form.cleaned_data.get('pending_adm_alt_id')

                for pending_id in [pending_adm_id, pending_adm_alt_id]: # This line was already indented correctly.
                    if pending_id:
                # S'assurer que pending_id est traité comme un entier/string valide
                        print(f"DEBUG: Traitement de l'utilisateur ID {pending_id}")
                        try:
                    # On utilise select_for_update pour éviter les accès concurrents
                            new_user = User.objects.select_for_update().get(id=pending_id)
                            new_user.code_cluster = cluster # This line was already indented correctly.
                            new_user.is_active = True
                    
                    # Attribution du groupe Admin
                            admin_group, _ = Group.objects.get_or_create(name='Admin')
                            new_user.groups.add(admin_group)
                            new_user.save()

                    # Envoi du courriel
                            envoyer_email_creation_utilisateur(new_user.id, self.request)
                            print(f"DEBUG: Email envoyé à {new_user.email}")
                    
                        except User.DoesNotExist:
                            print(f"DEBUG: Utilisateur {pending_id} introuvable")

                # 6. Synchronisation des groupes Admin
                new_admins = {cluster.admin_cluster, cluster.admin_alt_cluster} - {None}
                admin_group, created = Group.objects.get_or_create(name='Admin')

                # Retrait des droits pour les anciens qui ne sont plus admins
                for user in (old_admins - new_admins):
                    user.groups.remove(admin_group)
                    user.code_cluster = None
                    user.is_active = False
                    user.save()

                # Ajout des droits pour les nouveaux arrivants
                for user in (new_admins - old_admins):
                    user.groups.add(admin_group)
                    # Note : code_cluster est déjà géré par ClusterForm.save()

                # 6. Mise à jour des permissions spécifiques aux champs
                if self.user_has_any_permission_group(self.request.user):
                    self.update_field_permissions(cluster, form)

                messages.success(self.request, _("Le cluster {} a été mis à jour avec succès.").format(cluster.name_cluster))
                
                # Redirection directe pour éviter le double save de super().form_valid()
                return redirect(self.get_success_url())

        except Exception as e:
            messages.error(self.request, _("Une erreur est survenue lors de la mise à jour : ") + str(e))
            return self.form_invalid(form)