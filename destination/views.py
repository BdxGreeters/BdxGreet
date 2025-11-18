from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from destination.models import Destination
from core.models import FieldPermission
from destination.forms import DestinationForm
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views import View
from core.translation import DestinationTranslationOptions
from django.contrib import messages
from core.mixins import FieldPermissionMixin
from core.tasks import translation_content_items, translation_content
from django.utils.translation import gettext_lazy as _

User=get_user_model()


# Vue Création d'une destination
class SuperAdminRequiredMixin(UserPassesTestMixin):
    
    def test_func(self):
        return self.request.user.groups.filter(name__in=['SuperAdmin', 'Admin']).exists() 

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les droits nécessaires pour créer une destination.")
        return redirect('clusters_list')

class DestinationCreateView(LoginRequiredMixin, SuperAdminRequiredMixin,CreateView):
    template_name = 'destination/destination_form.html'
    success_url = reverse_lazy('destinations_list')
    permission_groups = ['SuperAdmin', 'Admin']  # Utilisez une liste pour les groupes de permission
    target_group_name = 'Referent'
    app_name = 'destination'

    def get(self, request, *args, **kwargs):
        form = DestinationForm(request.GET or None, user=request.user)
        context = {'form': form, 'title': _("Créer une destination")}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = DestinationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Sauvegarder l'instance de la destination
            destination= form.save(commit=False)
            destination.save()

            #Mettre à jour les groupes des utilisateurs liés à cette destination
            if destination.manager_dest:
                manager_group, created = Group.objects.get_or_create(name='Manager')
                destination.manager_dest.groups.add(manager_group)
        
            if destination.referent_dest:
                referent_group, created = Group.objects.get_or_create(name='Referent')
                destination.referent_dest.groups.add(referent_group)

            if destination.matcher_dest:
                matcher_group, created = Group.objects.get_or_create(name='Matcher')
                destination.matcher_dest.groups.add(matcher_group)  

            if destination.matcher_alt_dest:
                matcher_alt_group, created = Group.objects.get_or_create(name='Matcher_Alt')
                destination.matcher_alt_dest.groups.add(matcher_alt_group)

            if destination.finance_dest:
                finance_group, created = Group.objects.get_or_create(name='Financier')
                destination.finance_dest.groups.add(finance_group)

            destination.save()
            form.save_m2m()  # Sauvegarder les relations ManyToMany si nécessaire

            # Traduction des ieux ou thèmes de la destination
            for field in DestinationTranslationOptions.fields:
                translation_content_items.delay('destination', 'Destination', destination.id, field)
            
            # Traduction des types de handicap
            translation_content.delay("destination","Destination", destination.id, "disability_libelle_dest")

            messages.success(request, _("La destination  {} a été créée.").format(destination.name_dest))
            return redirect('destinations_list')
        
        else:
            messages.error(request, _("Le formulaire n'est pas valide."))
            context = {'form': form, 'title': _("Créer une destination")}
            return render(request, self.template_name, context)
        
###################################################################################################

# Vue Liste des destinations
 
class DestinationListView(LoginRequiredMixin, View):
    template_name = 'destination/destinations_list.html'

    def get(self, request, *args, **kwargs):
        destinations = Destination.objects.all()
        context = {'destinations': destinations, 'title': _("Liste des destinations")}
        return render(request, self.template_name, context) 
    
###################################################################################################

#Vue Ajax pour ren,voyer les informations d'une destination sélectionnée

# views.py
from django.http import JsonResponse


User = get_user_model()

class AjaxFilterUsersView(View):
    
    def get(self, request, *args, **kwargs):
        """
        Gère les requêtes GET pour filtrer les utilisateurs par cluster et destination.
        """
        cluster_code = request.GET.get('cluster_code')
        code_dest = request.GET.get('code_dest')
        print(f"Cluster Code: {cluster_code}, Destination Code: {code_dest}")
        
        # Si les codes ne sont pas fournis, on renvoie une liste vide
        if not cluster_code or not code_dest:
            return JsonResponse([], safe=False)
            
        # --- Logique de filtrage basée sur votre modèle CustomUser ---
        # On filtre directement sur les champs du modèle CustomUser
        users = User.objects.filter(
            code_cluster=cluster_code,
            code_dest=code_dest
        ).distinct()
        
        # Formattez les résultats pour le JSON
        # Une représentation textuelle plus claire pour le champ <select>
        results = [
            {
                "id": user.id, 
                "text": f"{user.first_name} {user.last_name} ({user.email})"
            }
            for user in users
        ]
        
        return JsonResponse(results, safe=False)
    
###################################################################################################

# Vue Wizard Création d'une destination

# votre_app/views.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from formtools.wizard.views import SessionWizardView
from .forms import DestinationForm, DestinationDataForm

# Stockage temporaire pour le logo pendant le wizard
temp_storage_location = os.path.join(settings.MEDIA_ROOT, 'wizard_tmp')
temp_storage = FileSystemStorage(location=temp_storage_location)

class DestinationCreationWizard(SessionWizardView):
    # Ordre des formulaires
    form_list = [DestinationForm, DestinationDataForm]
    
    # Template unique utilisé pour toutes les étapes
    template_name = 'destination/destination_wizard.html'
    
    # Indispensable pour gérer l'upload de fichier (logo_dest)
    file_storage = temp_storage

    def done(self, form_list, **kwargs):
        """
        Exécuté uniquement quand tout est valide à la fin.
        """
        # 1. Sauvegarde de la Destination (Parent)
        # Cela déplace aussi le logo du dossier temporaire vers 'logos/' 
        destination_form = form_list[0]
        destination_instance = destination_form.save()

        # 2. Sauvegarde de Destination_data (Enfant 1)
        data_form = form_list[1]
        destination_data = data_form.save(commit=False)
        # Création manuelle du lien OneToOne [cite: 148]
        destination_data.code_dest_data = destination_instance
        destination_data.save()

        # 3. Redirection finale
        return redirect('liste_destinations') # Remplacez par votre URL de succès