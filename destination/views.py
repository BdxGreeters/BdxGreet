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
from django.core.exceptions import PermissionDenied

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
                matcher_group, created = Group.objects.get_or_create(name='Gestionnaire')
                destination.matcher_dest.groups.add(matcher_group)  

            if destination.matcher_alt_dest:
                matcher_alt_group, created = Group.objects.get_or_create(name='Gestionnaire')
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
        user=request.user
        is_super_admin = user.groups.filter(name='SuperAdmin').exists()
        is_admin = user.groups.filter(name='Admin').exists()
        print("is_admin:", is_admin)
        if is_super_admin:
            destinations = Destination.objects.all()
        elif is_admin :
            user_code_cluster = user.code_cluster
            print("user_code_cluster:", user_code_cluster)
            destinations = Destination.objects.filter(code_cluster__code_cluster=user_code_cluster)
        else:
            # 3. Autres utilisateurs : Afficher une erreur d'autorisation 403
            # Ceci interrompt l'exécution de la vue et affiche la page d'erreur 403
            messages.error(request, _("Vous n'avez pas les droits nécessaires pour consulter la liste des destinations."))
            return redirect('login')  
        context = {'destinations': destinations, 'title': _("Liste des destinations")}
        return render(request, self.template_name, context) 
    
###################################################################################################

# Vue Détail d'une destination

class AuthorizedRequiredReadDestinationMixin(UserPassesTestMixin):
    

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

class DestinationDetailView(LoginRequiredMixin, AuthorizedRequiredReadDestinationMixin, DetailView):
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


class AuthorizedRequiredUpdateDestinationMixin(UserPassesTestMixin):
    

    def test_func(self):
    # Autoriser les SuperAdmin ou les utilisateurs qui sont admin du cluster
        destination = self.get_object()
        
        return (
            self.request.user.groups.filter(name = 'SuperAdmin').exists() or
            (self.request.user.groups.filter(name = 'Admin').exists() and
            self.request.user.code_cluster == destination.code_cluster.code_cluster) or
            self.request.user == destination.referent_dest or
            self.request.user == destination.matcher_dest or
            self.request.user == destination.matcher_alt_dest
            )

    def handle_no_permission(self):
        messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour éditer cette destination."))
        return redirect('destinations_list')

class DestinationUpdateView(LoginRequiredMixin, AuthorizedRequiredUpdateDestinationMixin,UpdateView):
    
    model = Destination
    form_class = DestinationForm
    template_name = 'destination/destination_update.html'
    context_object_name = 'destination'
    
    # Gestion de l'autorisation d'édition du champ 'statut_dest'
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        destination = self.get_object() # Récupère l'objet Destination en cours d'édition
        # Vérification SuperAdmin
        is_super_admin = user.groups.filter(name='SuperAdmin').exists()
        
        # Vérification Admin de Cluster
        is_admin_cluster_match = (
            user.groups.filter(name='Admin').exists() and
            user.code_cluster == destination.code_cluster.code_cluster
        )
        
        # Le champ est autorisé à l'édition si l'une des conditions est vraie
        can_edit_statut = is_super_admin or is_admin_cluster_match
        # Désactivation du champ si l'utilisateur N'EST PAS autorisé
        if not can_edit_statut:
            if 'statut_dest' in form.fields:
                form.fields['statut_dest'].disabled = True

        # Gestion de l'autorisation d'édition pour les champs autres que ceux du matcher

        matcher_fields = [
        'list_places_dest',
        'mini_lp_dest',
        'max_lp_dest',
        'mini_interest_center_dest',
        'max_interest_center_dest',
        'flag_stay_dest',
        'dispersion_param_dest'
        ]
        is_in_matcher=user.groups.filter(name='Gestionnaire').exists()
        print("is_in_matcher:", is_in_matcher)
        is_not_excluded= not user.groups.filter(name__in=['SuperAdmin','Admin','Referent']).exists()

        is_only_gestionnaire= is_in_matcher and is_not_excluded
        print("is_only_gestionnaire:", is_only_gestionnaire)
        if is_only_gestionnaire:
            all_form_fields = list(form.fields.keys())
            fields_to_disable = [
                field_name 
                for field_name in all_form_fields 
                if field_name not in matcher_fields
            ]

            for field_name in fields_to_disable:
                if field_name in form.fields:
                    form.fields[field_name].disabled = True
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indique que c'est une mise à jour
        return kwargs

    def form_valid(self, form):
        # Récuperer l'instance de la destinataion avant la sauvegarde
        old_destination = self.get_object()
        # Sauvegarder la destination
        destination = form.save(commit=False)
        destination.code_cluster = old_destination.code_cluster # 
        destination.save() 

        old_manager = {old_destination.manager_dest, old_destination.referent_dest} - {None}
        new_manager = {destination.manager_dest} - {None}
        

        manager_group, created = Group.objects.get_or_create(name='Manager')
        
        for user in old_manager - new_manager:
            user.groups.remove(manager_group)
            user.save()
        
        for user in new_manager - old_manager:
            user.groups.add(manager_group)
            user.save()

        old_referent = {old_destination.referent_dest} - {None}
        new_referent = {destination.referent_dest} - {None}
        referent_group, created = Group.objects.get_or_create(name='Referent')
        
        for user in old_referent - new_referent:
            user.groups.remove(referent_group)
            user.save()

        for user in new_referent - old_referent:
            user.groups.add(referent_group)
            user.save()

        old_matcher = {old_destination.matcher_dest, old_destination.matcher_alt_dest} - {None}
        new_matcher = {destination.matcher_dest, destination.matcher_alt_dest} - {None}
        matcher_group, created = Group.objects.get_or_create(name='Gestionnaire')

        for user in old_matcher - new_matcher:
            user.groups.remove(matcher_group)
            user.save()

        for user in new_matcher - old_matcher:
            user.groups.add(matcher_group)
            user.save()

        old_financier = {old_destination.finance_dest} - {None}
        new_financier = {destination.finance_dest} - {None}
        financier_group, created = Group.objects.get_or_create(name='Financier')

        for user in old_financier - new_financier:
            user.groups.remove(financier_group)
            user.save()

        for user in new_financier - old_financier:
            user.groups.add(financier_group)
            user.save()

        old_user={old_destination.manager_dest, old_destination.referent_dest, old_destination.matcher_dest, old_destination.matcher_alt_dest, old_destination.finance_dest} - {None}
        new_user={destination.manager_dest, destination.referent_dest, destination.matcher_dest, destination.matcher_alt_dest, destination.finance_dest} - {None}

        print("old_user:", old_user)
        print("new_user:", new_user)

        for user in old_user - new_user:
            user.code_dest=None
            user.save()

        for user in new_user - old_user:
            user.code_dest=destination.code_dest
            user.save()
        
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

        messages.success(self.request, _(f"La destination {self.object.name_dest} a été mise à jour."))
        return super().form_valid(form)
 
    def form_invalid(self, form):
        messages.error(self.request, _("Le formulaire n'est pas valide."))
        return super().form_invalid(form)

    def get_success_url(self):
        return redirect('destination_detail', pk=self.object.pk).url
    

###################################################################################################

# Vue Mixin pour les permissions de champ pour le gestionnaire de destination

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class OnlyGestionnaireMixin(AccessMixin):
    """
    Mixin pour restreindre la modification des champs.
    Il vérifie si l'utilisateur est STRICTEMENT 'Gestionnaire', 
    c'est-à-dire qu'il n'appartient à aucun des groupes à privilège supérieur.
    """
    
    # 🚨 DOIT ÊTRE DÉFINI DANS LA VUE QUI UTILISE LE MIXIN
    gestionnaire_fields = []
    
    # Les groupes qui accordent des privilèges supérieurs à 'Gestionnaire'
    higher_privilege_groups = ['SuperAdmin', 'Admin''Referent', 'Admin', 'SuperAdmin']
    
    
    def _is_only_gestionnaire(self, user):
        """ Logique interne de vérification des groupes. """
        if not user.is_authenticated:
            return False

        user_groups = user.groups.all().values_list('name', flat=True)

        is_gestionnaire = 'Gestionnaire' in user_groups
        has_higher_privilege = any(group in user_groups for group in self.higher_privilege_groups)

        # L'utilisateur est 'Gestionnaire' ET n'a AUCUN privilège supérieur.
        return is_gestionnaire and not has_higher_privilege

    
    def get_form(self, form_class=None):
        """ Modifie le formulaire en désactivant les champs non autorisés. """
        form = super().get_form(form_class)
        user = self.request.user
        
        # Appliquer la désactivation SEULEMENT si l'utilisateur est un 'Gestionnaire' simple
        if self._is_only_gestionnaire(user):
            if not self.gestionnaire_fields:
                # Cela empêche une erreur si la liste n'est pas définie dans la vue
                raise AttributeError(
                    "Le Mixin OnlyGestionnaireMixin nécessite que la liste 'gestionnaire_fields' soit définie dans la vue."
                )
                
            all_fields = list(form.fields.keys())
            
            # Déterminer les champs à désactiver
            fields_to_disable = [
                field for field in all_fields 
                if field not in self.gestionnaire_fields
            ]

            # Désactiver les champs dans le formulaire
            for field_name in fields_to_disable:
                if field_name in form.fields:
                    form.fields[field_name].disabled = True
                    
        return form