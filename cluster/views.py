from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from cluster.models import Cluster
from destination.models import Destination  
from core.models import FieldPermission
from cluster.forms import ClusterForm
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views import View
from core.translation import ClusterTranslationOptions
from django.contrib import messages
from core.mixins import FieldPermissionMixin
from core.tasks import translation_content_items
from django.utils.translation import gettext_lazy as _

User=get_user_model()


# Vue Création d'un cluster

class SuperAdminRequiredMixin(UserPassesTestMixin):
    
    def test_func(self):
        return self.request.user.groups.filter(name='SuperAdmin').exists() 

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les droits nécessaires pour créer un cluster.")
        return redirect('clusters_list')

class ClusterCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, FieldPermissionMixin, CreateView):
    template_name = 'cluster/cluster_form.html'
    success_url = reverse_lazy('clusters_list')
    permission_groups = ['SuperAdmin']  # Utilisez une liste pour les groupes de permission
    target_group_name = 'Admin'
    app_name = 'cluster'

    def get(self, request, *args, **kwargs):
        form = ClusterForm(request.GET or None, user=request.user)
        context = {'form': form, 'title': _("Créer un cluster")}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = ClusterForm(request.POST, user=request.user)
        if form.is_valid():
            # Sauvegarder l'instance du cluster
            cluster = form.save(commit=False)

            # Ajouter les groupes aux administrateurs
            admin_group, created = Group.objects.get_or_create(name='Admin')

            if cluster.admin_cluster:
                if not cluster.admin_cluster.pk:
                    cluster.admin_cluster.save()
                cluster.admin_cluster.groups.add(admin_group)

            if cluster.admin_alt_cluster:
                if not cluster.admin_alt_cluster.pk:
                    cluster.admin_alt_cluster.save()
                cluster.admin_alt_cluster.groups.add(admin_group)
                    
            cluster.save()

            # Mettre à jour les permissions si l'utilisateur appartient à un groupe autorisé
            if self.user_has_any_permission_group(request.user):
                self.update_field_permissions(cluster, form)
                messages.success(request, _("Cluster créé et permissions enregistrées avec succès."))
            else:
                messages.success(request, _("Cluster créé avec succès."))

            # Traduction des champs
            for field in ClusterTranslationOptions.fields:
                translation_content_items.delay('cluster', 'Cluster', cluster.id, field)

            messages.success(request, _("Le cluster {} a été créé.").format(cluster.name_cluster))
            return redirect('clusters_list')
        else:
            messages.error(request, _("Le formulaire n'est pas valide."))
            context = {'form': form, 'title': _("Créer un cluster")}
            return render(request, self.template_name, context)
        
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
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from core.translation import ClusterTranslationOptions
from core.mixins import FieldPermissionMixin
from core.tasks import translation_content_items
from .forms import ClusterForm
from .models import Cluster

class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        cluster = self.get_object()
        return (
            self.request.user.groups.filter(name='SuperAdmin').exists() or
            self.request.user == cluster.admin_cluster or
            self.request.user == cluster.admin_alt_cluster
        )

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour modifier un cluster."))
        return redirect('clusters_list')

class ClusterUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, FieldPermissionMixin, UpdateView):
    model = Cluster
    form_class = ClusterForm
    template_name = 'cluster/cluster_form.html'
    success_url = reverse_lazy('clusters_list')
    title = _("Modification du cluster")
    permission_groups = ['SuperAdmin']  # Liste des groupes autorisés
    target_group_name = 'Admin'
    app_name = 'cluster'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Désactiver les champs non modifiables pour les utilisateurs non autorisés
        if not self.user_has_any_permission_group(self.request.user):
            permissions = self.get_field_permissions(self.object)
            for field_name, is_editable in permissions.items():
                if not is_editable and field_name in form.fields:
                    form.fields[field_name].disabled = True
        form.fields['code_cluster'].disabled = True
        return form

    def form_valid(self, form):
        # Récupérer l'instance du cluster avant la sauvegarde
        old_cluster = self.get_object()
        # Sauvegarder le cluster
        cluster = form.save(commit=False)
        cluster.code_cluster = old_cluster.code_cluster
        cluster.save()

        # Récupérer les anciens et nouveaux administrateurs
        old_admins = {old_cluster.admin_cluster, old_cluster.admin_alt_cluster} - {None}
        new_admins = {cluster.admin_cluster, cluster.admin_alt_cluster} - {None}

        # Récupérer ou créer le groupe "Admin"
        admin_group, created = Group.objects.get_or_create(name='Admin')

        # Retirer du groupe Admin les utilisateurs qui ne sont plus administrateurs
        for user in old_admins - new_admins:
            user.groups.remove(admin_group)

        # Ajouter au groupe Admin les nouveaux administrateurs
        for user in new_admins - old_admins:
            user.groups.add(admin_group)

        # Traduction des champs
        for field in ClusterTranslationOptions.fields:
            translation_content_items.delay('cluster', 'Cluster', cluster.id, field)

        # Mettre à jour les permissions si l'utilisateur appartient à un groupe autorisé
        if self.user_has_any_permission_group(self.request.user):
            self.update_field_permissions(cluster, form)
            messages.success(self.request, _("Cluster et permissions mis à jour avec succès."))
        else:
            messages.success(self.request, _("Cluster mis à jour avec succès."))

        return super().form_valid(form)

####################################################################################################
