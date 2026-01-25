from django.contrib import messages as django_messages
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
from core.mixins import RelatedModelsMixin, HelpTextTooltipMixin
from core.models import FieldPermission
from core.tasks import translation_content, translation_content_items
from core.translation import DestinationTranslationOptions
from destination.forms import DestinationForm, DestinationDataForm, DestinationFluxForm
from destination.models import Destination, Destination_data, Destination_flux,List_places
from PIL import Image
import os
from django.db.models import Q   
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db import transaction
from core.tasks import envoyer_email_creation_utilisateur, resize_image_task
from destination.mixins import OnlyGestionnaireMixin

User=get_user_model()


# Vue Création d'une destination
class SuperAdminRequiredMixin(UserPassesTestMixin):
    
    def test_func(self):
        return self.request.user.groups.filter(name__in=['SuperAdmin', 'Admin']).exists() 

    def handle_no_permission(self):
        django_messages.error(self.request, "Vous n'avez pas les droits nécessaires pour créer une destination.")
        return redirect('clusters_list')

class DestinationCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, HelpTextTooltipMixin, RelatedModelsMixin, CreateView):
    model = Destination
    form_class = DestinationForm
    template_name = 'destination/destination_form.html'
    success_url = reverse_lazy('destinations_list') 
    
    app_name = 'destination'
    related_fields = {
        'list_places_dest': (List_places, 'list_places_dest', 'list_places_dest')
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Création d'une destination")
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'code_cluster_user': getattr(self.request.user, 'code_cluster', None)
        })
        return kwargs

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # A. Sauvegarde Destination
                self.object = form.save(commit=False)
                dest = self.object

                # --- LOGIQUE PARENT ---
                parent_dest = form.cleaned_data.get('code_parent_dest')
                if parent_dest:
                # On force les valeurs du parent si elles existent
                    dest.manager_dest = parent_dest.manager_dest
                    dest.referent_dest = parent_dest.referent_dest
                
                
                # Gestion code_cluster (depuis champ masqué ou form)
                h_cluster = self.request.POST.get('code_cluster_hidden')
                dest.code_cluster = h_cluster if h_cluster else form.cleaned_data.get('code_cluster')
                dest.save()

                # B. Mixin (Tags/Lieux)
                self.save_related_data(form)

                # C. Activation des Users "Pending" (AJAX)
                user_roles = {
                    'manager_dest': 'Manager', 'referent_dest': 'Referent',
                    'matcher_dest': 'Gestionnaire', 'matcher_alt_dest': 'Gestionnaire',
                    'finance_dest': 'Financier',
                }
                
                users_to_notify = set()

                for field, group_name in user_roles.items():
                    user_obj = form.cleaned_data.get(field)
                    print(f"Traitement de l'utilisateur pour le champ {field}: {user_obj}")
                    if user_obj:
                        user_obj.is_active = True
                        user_obj.code_cluster = dest.code_cluster
                        user_obj.code_dest = dest
                        user_obj.save()
                        
                        group,created= Group.objects.get_or_create(name=group_name)
                        user_obj.groups.add(group)

                        users_to_notify.add(user_obj)

                        
                for user_obj in users_to_notify:
                    # Email via Celery (on_commit est préférable pour éviter les Race Conditions)
                    transaction.on_commit(
                        lambda u_id=user_obj.id: envoyer_email_creation_utilisateur(u_id, self.request)
                    )        
                        
                        

                # D. Traduction des types de handicap et logo
              
                if dest.disability_libelle_dest:
                    transaction.on_commit(
                        lambda: translation_content.delay("destination", "Destination", dest.id, "disability_libelle_dest")
                    )
                if dest.logo_dest:
                    transaction.on_commit(lambda: 
                        resize_image_task.delay(
                            app_label='destination', 
                            model_name='Destination', 
                            object_id=dest.id, 
                            field_name='logo_dest', 
                            width=200, 
                            height=200
                        )
                    )       
                
                # E. Message & Redirection
                django_messages.success(self.request, _("Destination créée et comptes activés."))
                return redirect('create_related_data', destination_id=dest.id)

        except Exception as e:
            print("Erreur lors de la création de la destination :", str(e))
            django_messages.error(self.request, f"Erreur : {str(e)}")
            return self.form_invalid(form)
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
        django_messages.error(request, _("Le formulaire n'est pas valide."))
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
            

            django_messages.success(request, _("La destination {} a été créée.").format(destination.name_dest))
            return redirect('destination_detail', pk=destination.id)

        context = {
            'destination': destination,
            'flux_form': flux_form,
          
        }
        django_messages.error(request, _("Le formulaire n'est pas valide."))
        return render(request, 'destination/create_related_flux.html', context)

###################################################################################################
# Vue Liste des destinations
 
class DestinationListView(LoginRequiredMixin, View):
    template_name = 'destination/destinations_list.html'

    def get(self, request, *args, **kwargs):
        user=request.user
        is_super_admin = user.groups.filter(name='SuperAdmin').exists()
        is_admin = user.groups.filter(name='Admin').exists()
        is_referent = user.groups.filter(name='Referent').exists()
        is_gestionnaire = user.groups.filter(name='Gestionnaire').exists()
        is_financier = user.groups.filter(name='Financier').exists()
        is_manager = user.groups.filter(name='Manager').exists()

        if is_super_admin:
            destinations = Destination.objects.all()
        elif is_admin :
            user_code_cluster = user.code_cluster
            print("user_code_cluster:", user_code_cluster)
            destinations = Destination.objects.filter(code_cluster__code_cluster=user_code_cluster)
        elif is_referent or is_gestionnaire or is_financier or is_manager:
            destinations = Destination.objects.filter(Q(manager_dest=user) | Q(referent_dest=user) | Q(matcher_dest=user) | Q(matcher_alt_dest=user) | Q(finance_dest=user))        
        else:
            django_messages.error(request, _("Vous n'avez pas les droits nécessaires pour consulter la liste des destinations."))
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
        django_messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour consulter cette destination."))
        return redirect('destinations_list')

class DestinationDetailView(LoginRequiredMixin, AuthorizedRequiredReadDestinationMixin, DetailView):
    model = Destination
    template_name = 'destination/destination_detail.html'
    context_object_name = 'destination'
    
    



###################################################################################################

#Vue Ajax pour renvoyer les informations d'une destination sélectionnée

from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class AjaxFilterUsersView(View):
    def get(self, request, *args, **kwargs):
        cluster_code = request.GET.get('code_cluster')
        code_dest = request.GET.get('code_dest')
        print("Cluster code (AJAX):", cluster_code)
        print("Code destination (AJAX):", code_dest)

        if not cluster_code:
            return JsonResponse([], safe=False)

        # Récupération du code parent (sécurité héritage)
        parent_code = None
        if code_dest:
            from .models import Destination
            dest_obj = Destination.objects.filter(code_dest=code_dest).first()
            if dest_obj and dest_obj.code_parent_dest:
                parent_code = dest_obj.code_parent_dest.code_dest

        # CONSTRUCTION DE LA QUERY
        # 1. Les Pendings : Critère de fiabilité absolue selon votre workflow
        query_pending = Q(is_active=False)

        # 2. Les Actifs autorisés : Doivent être dans le même Cluster
        # ET (être dans la destination actuelle OU la destination parente)
        query_authorized_active = Q(
            is_active=True,
            code_cluster__code_cluster=cluster_code
        )
        
        dest_filter = Q(code_dest__code_dest=code_dest) | Q(code_dest__isnull=True)
        if parent_code:
            dest_filter |= Q(code_dest__code_dest=parent_code)
            
        query_authorized_active &= dest_filter

        # Union des deux groupes
        users = User.objects.filter(query_pending | query_authorized_active).distinct().order_by('last_name', 'first_name')
        
        results = [
            {
                "id": user.id, 
                "text": f"{user.first_name} {user.last_name}",
                "is_active": user.is_active
            } 
            for user in users
        ]
        
        return JsonResponse(results, safe=False)

###################################################################################################
# AJAX pour récuperer les managers et référents de la destination parent pour une destination donnée

from django.http import JsonResponse
@LoginRequiredMixin
def get_parent_destination_info(request):
    parent_id = request.GET.get('parent_id')
    try:
        parent = Destination.objects.get(pk=parent_id)
        return JsonResponse({
            'manager_id': parent.manager_dest.id if parent.manager_dest else '',
            'referent_id': parent.referent_dest.id if parent.referent_dest else '',
        })
    except Destination.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

###################################################################################################
# Vue Mise à jour d'une destination

class AuthorizedRequiredUpdateDestinationMixin(UserPassesTestMixin):
    

    def test_func(self):
    # Autoriser les SuperAdmin, les Admin du cluster de la destination ou les utilisateurs qui sont référents ou gestionnaires
        obj = self.get_object()
        if isinstance(self, DestinationUpdateView):
        # Ici obj est une 'Destination'
            destination = obj
        elif isinstance(self, DestinationDataUpdateView):
        # Ici obj est un 'DestinationData', on remonte à la destination parente
        # (Adaptez 'destination' selon le nom de votre ForeignKey dans DestinationData)
            destination = obj.code_dest_data
        elif isinstance(self, DestinationFluxUpdateView):
        # Ici obj est un 'DestinationFlux', on remonte à la destination parente 
            destination = obj.code_dest_flux 
        else:
            return False
            
        
        return (
            self.request.user.groups.filter(name = 'SuperAdmin').exists() or
            (self.request.user.groups.filter(name = 'Admin').exists() and
            self.request.user.code_cluster == destination.code_cluster.code_cluster) or
            self.request.user == destination.referent_dest or
            self.request.user == destination.matcher_dest or
            self.request.user == destination.matcher_alt_dest
            )

    def handle_no_permission(self):
        django_messages.error(self.request, _("Vous n'avez pas les droits nécessaires pour éditer cette destination."))
        return redirect('destinations_list')


class DestinationUpdateView(LoginRequiredMixin, AuthorizedRequiredUpdateDestinationMixin, OnlyGestionnaireMixin,HelpTextTooltipMixin, RelatedModelsMixin, UpdateView):
    model = Destination
    form_class = DestinationForm
    template_name = 'destination/destination_form.html'
    success_url = reverse_lazy('destinations_list')
    
    app_name = 'destination'

    related_fields = {
        'list_places_dest': (List_places, 'list_places_dest', 'list_places_dest')
    }
    

    def get_initial(self):
        initial = super().get_initial()
        destination = self.get_object()
        
        # Pré-remplissage des champs texte (tags) à partir des relations M2M
        for form_field, (model, m2m_field, model_attr) in self.related_fields.items():
            existing_values = getattr(destination, m2m_field).values_list(model_attr, flat=True)
            initial[form_field] = ', '.join(existing_values)
        return initial

    gestionnaire_fields = [
        'list_places_dest',
        'mini_lp_dest',
        'max_lp_dest',
        'mini_interest_center_dest',
        'max_interest_center_dest',
        'flag_stay_dest',
        'dispersion_param_dest'
        ]
    
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
                form.fields['code_IGA_dest'].disabled = True
    
        if destination.code_parent_dest:
            if 'code_parent_dest' in form.fields:
                form.fields['code_parent_dest'].disabled = True
                form.fields['manager_dest'].disabled = True
                form.fields['referent_dest'].disabled = True


        return form

        

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indique que c'est une mise à jour
        return kwargs




    def form_valid(self, form):

        user_roles_map = {
            'manager_dest': 'Manager', 
            'referent_dest': 'Referent',
            'matcher_dest': 'Gestionnaire', 
            'matcher_alt_dest': 'Gestionnaire',
            'finance_dest': 'Financier',
        }

        try:
            with transaction.atomic():
                # 1. Instance avant modification
                old_instance = Destination.objects.get(pk=self.object.pk)
                
                # 2. Sauvegarde de l'instance actuelle
                dest = form.save()
                
                h_cluster = self.request.POST.get('code_cluster_hidden')
                dest.code_cluster = h_cluster if h_cluster else form.cleaned_data.get('code_cluster')
                dest.save()

                # 3. Données liées
                self.save_related_data(form)

                # 4. GESTION DES ROLES AVEC VÉRIFICATION
                for field, group_name in user_roles_map.items():
                    print(f"Vérification du champ {field} pour les modifications de rôle.") 
                    if field in form.changed_data:
                        old_user = getattr(old_instance, field)
                        print(f"Ancien utilisateur pour le champ {field}: {old_user}")
                        new_user = form.cleaned_data.get(field)
                        print(f"Nouveau utilisateur pour le champ {field}: {new_user}")

                        # --- A. NETTOYAGE DE L'ANCIEN UTILISATEUR ---
                        if old_user and old_user != new_user:
                            print(f"Nettoyage de l'ancien utilisateur pour le champ {field}: {old_user}")
                            group=Group.objects.filter(name=group_name).first()
                            print(f"Vérification du groupe {group_name}")
                            print(f"Groupe trouvé : {group}")
                            if group:
                                still_has_role_for_his_group=False
                                for f, g_name in user_roles_map.items():
                                    print(f"Vérification du champ {f} avec le groupe {g_name}")
                                    if g_name == group_name :
                                        if getattr(dest, f) == old_user:
                                            still_has_role_for_his_group=True
                                            break
                                if not still_has_role_for_his_group:
                                    old_user.groups.remove(group)
                                
                                is_completely_unassigned = not any(
                                    getattr(old_instance, f) == old_user for f in user_roles_map.keys()
                                )
                                if is_completely_unassigned:
                                    old_user.is_active = False
                                    old_user.code_cluster = None
                                    old_user.code_dest = None
                                    old_user.save()
                                            
                                

                        # --- B. CONFIGURATION DU NOUVEL UTILISATEUR ---
                        if new_user:
                            new_user.is_active = True
                            new_user.code_cluster = dest.code_cluster
                            new_user.code_dest = dest
                            new_user.save()
                            
                            group, created = Group.objects.get_or_create(name=group_name)
                            new_user.groups.add(group)
                            
                            # On n'envoie l'email que s'il n'était pas déjà là dans un autre rôle
                            # (Optionnel : selon si vous voulez notifier à chaque nouveau rôle)
                            was_already_in_dest = any(
                                getattr(old_instance, f) == new_user for f in user_roles_map.keys()
                            )
                            if not was_already_in_dest:
                                envoyer_email_creation_utilisateur(new_user.id, self.request)

                # 5. IMAGE ET TRADUCTION
                if 'logo_dest' in form.changed_data and dest.logo_dest:
                    transaction.on_commit(lambda: 
                        resize_image_task.delay(
                            app_label='destination', 
                            model_name='Destination', 
                            object_id=dest.id, 
                            field_name='logo_dest', 
                            width=200, 
                            height=200
                        )
                    )

                if 'disability_libelle_dest' in form.changed_data and dest.disability_libelle_dest:
                    transaction.on_commit(
                        lambda: translation_content.delay("destination", "Destination", dest.id, "disability_libelle_dest")
                    )

                django_messages.success(self.request, _("Destination mise à jour avec succès."))
                return redirect(self.success_url)

        except Exception as e:
            django_messages.error(self.request, f"Erreur : {str(e)}")
            return self.form_invalid(form)

###################################################################################################

# M%ise à jour des données fonctionnelles destination_data

class DestinationDataUpdateView(LoginRequiredMixin, AuthorizedRequiredUpdateDestinationMixin, OnlyGestionnaireMixin ,UpdateView):
    
    model = Destination_data
    form_class = DestinationDataForm
    template_name = 'destination/destination_data_update.html'

    
    gestionnaire_fields = [
            'tripadvisor_dest',
            'googlemybusiness_dest',
            'flag_modalités_dest',
            'date_cg_mail_dest',
            'periode_mail_cg_dest',
            'flag_cg_T_dest',
            'flag_cg_U_dest',
            'flag_comment_visitor_dest',
            'param_comment_visitor_dest',
            'libelle_form_coche1_dest',
            'lib_url_form_coche1_dest',
            'url_form_coche1_dest',
            'libelle_form_coche2_dest',
            'lib_url_form_coche2_dest',
            'url_form_coche2_dest',
            'libelle_form_coche3_dest',
            'lib_url_form_coche3_dest',
            'url_form_coche3_dest',
            'flag_request_coche1_dest',
            'flag_request_coche2_dest',
            'flag_request_coche3_dest',
            'avis_fermeture_dest',
            'date_début_avis_fermeture_dest',
            'date_fin_avis_fermeture_dest',
            'texte_avis_fermeture_dest',
            'nbre_participants_fermeture_dest',
            'name_sign_mail_dest',
            'url_mail_signature_dest',
            'libelle_social1_mail_dest',
            'url_social1_mail_dest',
            'libelle_social2_mail_dest',
            'url_social2_mail_dest',
            'tagline_mail_dest',
            'titre_avis_mail_dest',
            'texte_avis_mail_dest',
            'date_debut_avis_mail_dest',
            'date_fin_avis_mail_dest'
        ]
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return form
        
    def form_valid(self, form):
        form.save()
        django_messages.success(self.request, _(f"Les données fonctionnelles de la destination {self.object.code_dest_data.name_dest} ont été mises à jour."))
        return super().form_valid(form)


    def form_invalid(self, form):
        django_messages.error(self.request, _("Le formulaire n'est pas valide."))
        return super().form_invalid(form)

    def get_success_url(self):
        return redirect('destination_detail', pk=self.object.code_dest_data.pk).url
        
###################################################################################################

# Mise à jour des données de flux de la destination

class DestinationFluxUpdateView(LoginRequiredMixin, AuthorizedRequiredUpdateDestinationMixin, OnlyGestionnaireMixin ,UpdateView):
    
    model = Destination_flux
    form_class = DestinationFluxForm
    template_name = 'destination/destination_flux_update.html'

    gestionnaire_fields =[]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        return form
        
    def form_valid(self, form):
        form.save()
        django_messages.success(self.request, _(f"Les données de flux de la destination {self.object.code_dest_flux.name_dest} ont été mises à jour."))
        return super().form_valid(form)


    def form_invalid(self, form):
        django_messages.error(self.request, _("Le formulaire n'est pas valide."))
        return super().form_invalid(form)

    def get_success_url(self):
        return redirect('destination_detail', pk=self.object.code_dest_flux.pk).url
###################################################################################################
