from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView
from core.mixins import FieldPermissionMixin
from core.models import FieldPermission
from core.tasks import translation_content, translation_content_items
from core.translation import DestinationTranslationOptions
from destination.forms import DestinationForm, DestinationDataForm, DestinationFluxForm
from destination.models import Destination, Destination_data, Destination_flux
from PIL import Image
import os
from django.conf import settings


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
                print(destination.manager_dest)
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

            # Redimension du logo en 200*200px
            img_path=os.path.join(settings.MEDIA_ROOT, str(destination.logo_dest.name))
            img = Image.open(img_path)
            img.thumbnail ((200,200))
            img.save(img_path)


            destination.save()
            form.save_m2m()  # Sauvegarder les relations ManyToMany si nécessaire

            # Traduction des ieux ou thèmes de la destination
            for field in DestinationTranslationOptions.fields:
                translation_content_items.delay('destination', 'Destination', destination.id, field)
            
            # Traduction des types de handicap
            if destination.disability_libelle_dest:
                translation_content.delay("destination","Destination", destination.id, "disability_libelle_dest")
            
            # Création automatique de Destination_data et Destination_flux
            return redirect('create_related_data', destination_id=destination.id)

        else:
            messages.error(request, _("Le formulaire n'est pas valide."))
            context = {'form': form, 'title': _("Créer une destination")}
            return render(request, self.template_name, context)
        
###################################################################################################

#Vue Création Destination_data

class CreateRelatedDataModelsView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    def get(self, request, destination_id):
        destination = Destination.objects.get(pk=destination_id)
        # Initialiser les formulaires avec l'instance de destination
        data_form = DestinationDataForm(initial={'code_dest_data': destination})
        
        context = {
            'destination': destination,
            'data_form': data_form,
        }
        return render(request, 'destination/create_related_data.html', context)

    def post(self, request, destination_id):
        destination = Destination.objects.get(pk=destination_id)

        # Récupérer les formulaires soumis
        data_form = DestinationDataForm(request.POST)
       

        if data_form.is_valid(): 
            # Sauvegarder Destination_data
            destination_data = data_form.save(commit=False)
            destination_data.code_dest_data = destination
            destination_data.save()
            data_form.save_m2m()  # Sauvegarder les relations ManyToMany

            return redirect('create_related_flux', pk=destination.id)

        context = {
            'destination': destination,
            'data_form': data_form,
          
        }
        messages.error(request, _("Le formulaire n'est pas valide."))
        return render(request, 'destination/create_related_data.html', context)

###################################################################################################

# Vue Création DestinationFlux

class CreateRelatedFluxModelsView(LoginRequiredMixin, SuperAdminRequiredMixin, View):
    def get(self, request, destination_id):
        destination = Destination.objects.get(pk=destination_id)
        # Initialiser les formulaires avec l'instance de destination
        flux_form = DestinationFluxForm(initial={'code_dest_flux': destination})
        
        context = {
            'destination': destination,
            'flux_form': flux_form,
        }
        return render(request, 'destination/create_related_flux.html', context)

    def post(self, request, destination_id):
        destination = Destination.objects.get(pk=destination_id)

        # Récupérer les formulaires soumis
        flux_form = DestinationFluxForm(request.POST)
       

        if flux_form.is_valid(): 
            # Sauvegarder Destination_data
            destination_flux = flux_form.save(commit=False)
            destination_flux.code_dest_flux = destination
            destination_flux.save()
            

            messages.success(request, _("La destination {} a été créée.").format(destination.name_dest))
            return redirect('destination/<int:pk>/destination/', pk=destination.id)

        context = {
            'destination': destination,
            'flux_form': flux_form,
          
        }
        messages.error(request, _("Le formulaire n'est pas valide."))
        return render(request, 'destination/create_related_flux.html', context)

###################################################################################################
# Vue Liste des destinations
 
class DestinationListView(LoginRequiredMixin, View):
    template_name = 'destination/destinations_list.html'

    def get(self, request, *args, **kwargs):
        destinations = Destination.objects.all()
        context = {'destinations': destinations, 'title': _("Liste des destinations")}
        return render(request, self.template_name, context) 
    
###################################################################################################

# Vue Détail d'une destination 

class DestinationDetailView(DetailView):
    model = Destination
    template_name = 'destination/destination_detail.html'
    context_object_name = 'destination'
    


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

