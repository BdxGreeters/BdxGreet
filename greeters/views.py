from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.db import transaction
from greeters.forms import GreeterCombinedForm
from greeters.models import Greeter
from destination.models import Destination
from cluster.models import Cluster
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.contrib import messages as django_messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from core.tasks import envoyer_email_creation_utilisateur, resize_image_task

User = get_user_model()

class AuthorRequiredCreateGreeterMixin(UserPassesTestMixin):
    
    def test_func(self):
        allowed_groups = ['SuperAdmin','Admin','Referent']
        return self.request.user.is_authenticated and self.request.user.groups.filter(name__in=allowed_groups).exists()
    
    def handle_no_permission(self):
        django_messages.error(self.request, "Vous n'avez pas les droits nécessaires pour créer un Greeter.")
        return redirect('login')

class GreeterCreateView(LoginRequiredMixin,AuthorRequiredCreateGreeterMixin,CreateView):
    model = Greeter
    form_class = GreeterCombinedForm
    template_name = 'greeters/greeter_form.html'
    success_url = reverse_lazy('login')
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs() 
        kwargs['admin_greeter'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        admin = self.request.user 
        code_cluster = getattr(admin, 'code_cluster', None)
        code_dest = getattr(admin, 'code_dest', None)
        if code_cluster:
            initial['cluster'] = code_cluster
        if code_dest:
            initial['destination'] = code_dest
            destination = Destination.objects.select_related('country_dest').get(code_dest=code_dest)
            initial['country_greeter']   = destination.country_dest
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
                    'lang_com': form.cleaned_data['lang_com'].code if form.cleaned_data['lang_com'] else None,
                    'code_cluster': form.cleaned_data['cluster'],
                    'code_dest': form.cleaned_data['destination'],
                }
                #print(f"Création de l'utilisateur avec les données: {user_data}")
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

                # 6. Message de succès et Redirection
                django_messages.success(self.request, _("Le greeter {} a été créé avec succès.").format(greeter.user.first_name + " " + greeter.user.last_name ))
              

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


###################################################################################################

#Vue Ajax pour mettre à jour dynamiquement les destinations, le pays et les langues de communication disponibles, les centres d'intérêts, expérioences Greeter, thèmes  en fonction de la destination sélectionnée dans le formulaire de création ou de mise à jour d'un Greeter
from django.db import models
from django.http import JsonResponse
from cluster.models import Cluster
from destination.models import Destination, Destination_data, Language_communication

def get_cluster_dest_data(request):
    # Récupération des IDs depuis la requête AJAX
    id_cluster = request.GET.get('code_cluster')
    id_dest = request.GET.get('code_dest')
    
    print(f"Requête AJAX reçue avec id_cluster={id_cluster} et id_dest={id_dest}")
    
    data = {
        'interests': [],
        'experiences': [],
        'langs': [],
        'places': [],
        'default_lang': None,
        'pays_id': None,
        'pays_name': None
    }

    try:
        # 1. Traitement du Cluster (Destinations, Intérêts et Expériences)
        if id_cluster and id_cluster.isdigit():
            cluster = Cluster.objects.filter(id=id_cluster).first()
            print(f"Cluster trouvé: {cluster}") 
            if cluster:
                #Récupération des destinations liées au cluster
                destinations = Destination.objects.filter(code_cluster=cluster).order_by('name_dest')    
                data['destinations'] = list(destinations.values('id', name=models.F('code_dest')))
                # Récupération des centres d'intérêt et des expériences liés au cluster
                data['interests'] = list(cluster.interest_center.values('id', name=models.F('interest_center')))
                data['experiences'] = list(cluster.experience_greeter.values('id', name=models.F('experience_greeter')))
        # 2. Traitement de la Destination (Pays, Lieux et Langues)
        if id_dest and id_dest.isdigit():
            dest = Destination.objects.filter(id=id_dest).first()
            if dest:
                # Récupération des lieux (votre erreur indiquait le champ 'list_places_dest')
                data['places'] = list(dest.list_places_dest.values('id', 'list_places_dest'))
                data['pays_id'] = dest.country_dest.id
                data['pays_name'] = dest.country_dest.nom_pays
                # Récupération des données liées via le OneToOneField (related_name='destination_data')
                # On utilise filter().first() pour éviter l'erreur si la relation n'existe pas
                dest_data = Destination_data.objects.filter(code_dest_data=dest).first()
                
                if dest_data:
                    # Gestion des langues
                    lang_ids = list(dest_data.langs_com_dest.values_list('id', flat=True))
                    if dest_data.lang_default_dest:
                        lang_ids.append(dest_data.lang_default_dest.id)
                    
                    langs = Language_communication.objects.filter(id__in=lang_ids).distinct()
                    print(f"Langues trouvées pour la destination: {langs}")
                    data['langs'] = list(langs.values('id', 'name'))
                    
                    if dest_data.lang_default_dest:
                        data['default_lang'] = dest_data.lang_default_dest.id

        return JsonResponse(data)

    except Exception as e:
        print(f"Erreur Python dans la vue : {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)