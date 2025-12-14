from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render
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
        code_cluster_user = getattr(request.user, 'code_cluster', None)
        form = DestinationForm(request.GET or None, user=request.user, code_cluster_user=code_cluster_user)
        context = {'form': form, 'title': _("Création d'une destination")}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        code_cluster_user = getattr(request.user, 'code_cluster', None)
        form = DestinationForm(request.POST, request.FILES, user=request.user, code_cluster_user=code_cluster_user)
        if form.is_valid():
            # Sauvegarder l'instance de la destination
            destination= form.save(commit=False)
            final_code_cluster= request.POST.get('code_cluster_hidden')
            if final_code_cluster is None:
                final_code_cluster=form.cleaned_data.get('code_cluster')
            if final_code_cluster:
                destination.code_cluster=final_code_cluster    
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

            # Redimension du logo en 200*200px
            img_path=os.path.join(settings.MEDIA_ROOT, str(destination.logo_dest.name))
            img = Image.open(img_path)
            img.thumbnail ((200,200))
            img.save(img_path)


            destination.save()
            form.save_m2m()  # Sauvegarder les relations ManyToMany si nécessaire

            # Traduction des lieux ou thèmes de la destination
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
        cluster=destination.code_cluster
        # Récupérer les formulaires soumis
        data_form = DestinationDataForm(request.POST, cluster_instance=cluster )

        if data_form.is_valid(): 
            # Sauvegarder Destination_data
            destination_data = data_form.save(commit=False)
            destination_data.code_dest_data = destination
            destination_data.save()
            data_form.save_m2m()  # Sauvegarder les relations ManyToMany

            # Traduction des champs 
            if destination_data.donation_text_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "donation_text_dest")
            if destination_data.param_comment_visitor_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "param_comment_visitor_dest")
            if destination_data.libelle_form_coche1_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "libelle_form_coche1_dest")
            if destination_data.lib_url_form_coche1_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "lib_url_form_coche1_dest")
            if  destination_data.libelle_form_coche2_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "libelle_form_coche2_dest")
            if  destination_data.lib_url_form_coche2_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "lib_url_form_coche2_dest")
            if  destination_data.libelle_form_coche3_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "libelle_form_coche3_dest")
            if  destination_data.lib_url_form_coche3_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "lib_url_form_coche3_dest")
            if  destination_data.texte_avis_fermeture_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "texte_avis_fermeture_dest")
            if destination_data.tagline_mail_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "tagline_mail_dest")
            if destination_data.titre_avis_mail_dest:
                translation_content.delay("destination","Destination_data", destination_data.id, "titre_avis_mail_dest")

            return redirect('create_related_flux', destination_id=destination.id)

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
            return redirect('destination_detail', pk=destination.id)

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

class AuthorizedRequiredMixin(UserPassesTestMixin):
    

    def test_func(self):
    # Autoriser les SuperAdmin ou les utilisateurs qui sont admin du cluster
        destination = self.get_object()
        
        return (
            self.request.user.groups.filter(name = 'SuperAdmin').exists() or
            (self.request.user.groups.filter(name = 'Admin').exists() and
            self.request.user.code_cluster == destination.code_cluster.code_cluster) or
            self.request.user == destination.manager_dest or
            self.request.user == destination.referent_dest or
            self.request.user == destination.matcher_dest or
            self.request.user == destination.matcher_alt_dest or
            self.request.user == destination.finance_dest
            )

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour consulter cette destination."))
        return redirect('destinations_list')

class DestinationDetailView(LoginRequiredMixin, AuthorizedRequiredMixin, DetailView):
    model = Destination
    template_name = 'destination/destination_detail.html'
    context_object_name = 'destination'
    
   
    



###################################################################################################

#Vue Ajax pour renvoyer les informations d'une destination sélectionnée

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


#Vue Mise à jour d'une destination



class DestinationUpdateView(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    
    model = Destination
    form_class = DestinationForm
    template_name = 'destination/destination_update.html'
    context_object_name = 'destination'

    def test_func(self):
        return self.request.user.groups.filter(name__in=['SuperAdmin', 'Admin', 'Referent', 'Gestionnaire']).exists()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indique que c'est une mise à jour
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Mise à jour de la destination")
        return context

    def form_valid(self, form):
        messages.success(self.request, _(f"La destination {self.object.name_dest} a été mise à jour."))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Le formulaire n'est pas valide."))
        return super().form_invalid(form)

    def get_success_url(self):
        return redirect('destination_detail', pk=self.object.pk).url