import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.forms import (BeneficiaireCreationForm, Email_MailjetCreationForm,
                        LangueDeepLCreationForm,
                        No_showCreationForm, PeriodeCreationForm,
                        TrancheAgeCreationForm, Types_handicapCreationForm)
from core.models import (Beneficiaire, Email_Mailjet,
                         Language_communication, LangueDeepL, No_show, Periode,
                         TrancheAge, Types_handicap)
from core.tasks import envoyer_email_creation_utilisateur, translation_content
from core.translator import translate


# Vue création d'un email_mAILJET
class Email_MailjetCreateView(View):
    def get(self, request, *args, **kwargs):
        form = Email_MailjetCreationForm()
        context = {'form': form, 'title':_("Créer un modèle d'email Mailjet")}
        return render(request, 'core/email_mailjet_form.html', context)

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = Email_MailjetCreationForm(request.POST)
            if form.is_valid():
                email_mailjet=form.save()
                messages.success(request, _("Le modèle d'email Mailjet {} a été créé.").format(email_mailjet.name_email))
                return redirect('email_mailjet_list')
            context = {'form': form, 'title':_("Créer un modèle d'email Mailjet")}
            return render(request, 'core/email_mailjet_form.html', context)
###################################################################################################

# Vue liste des emails Mailjet
class Email_MailjetListView(View):
    def get(self, request, *args, **kwargs):
        emails_Mailjet = Email_Mailjet.objects.all().order_by('name_email')
        return render(request, 'core/email_mailjet_list.html', {'emails_Mailjet': emails_Mailjet})
###################################################################################################

# Vue modification d'un email Mailjet
class Email_MailjetUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        email_Mailjet = get_object_or_404(Email_Mailjet, pk=pk)
        form = Email_MailjetCreationForm(instance=email_Mailjet)
        context = {'form': form, 'title':_("Modifier un modèle d'email Mailjet")}   
        return render(request, 'core/email_mailjet_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        email_mailjet = get_object_or_404(Email_Mailjet, pk=pk)
        form = Email_MailjetCreationForm(request.POST)
        if form.is_valid():
            email_mailjet=form.save()
            messages.success(request, _("Le modèle d'email Mailjet {} a été modifié.").format(email_mailjet.name_email))
            return redirect('email_mailjet_list')
        return render(request, 'core/email_mailjet_form.html', {'form': form, 'title':_("Modifier un modèle d'email Mailjet")})
###################################################################################################

# Vue création d'une langue prise en charge par Deepl et traduction dans les langues de communication
class LangueDeepLCreateView(View):
    def get(self, request, *args, **kwargs):
        form = LangueDeepLCreationForm()
        context = {'form': form, 'title':_("Créer une langue prise en charge par Deepl")}
        return render(request, 'core/langue_deepl_form.html', context)

    def post(self, request, *args, **kwargs):
        form = LangueDeepLCreationForm(request.POST)
        if form.is_valid():
            lang_deepl=form.save()
            messages.success(request, _("La langue {} a été prise en charge par Deepl.").format(lang_deepl.lang_deepl))
            return redirect('langue_deepl_list')
        context = {'form': form, 'title':_("Créer une langue prise en charge par Deepl")}
        return render(request, 'core/langue_deepl_form.html', context)
###################################################################################################

# Vue liste des langues prises en charge par Deepl
class LangueDeeplListView(View):
    def get(self,request, *args,**kwargs):
        langueDeepl= LangueDeepL.objects.all().order_by('nom_frncais')
        return  render(request, 'core/langue_deepl_list.html', {'langs_deepl': langueDeepl})
###################################################################################################

# Vue modification d'une langue prise en charge par Deepl
class LangueDeepLUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        langueDeepL = get_object_or_404(LangueDeepL, pk=pk)
        form = LangueDeepLCreationForm(instance=langueDeepL)
        context = {'form': form, 'title':_("Modifier une langue prise en charge par Deepl")}
        return render(request, 'core/langue_deepl_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        lang_deepl = get_object_or_404(LangueDeepL, pk=pk)
        form = LangueDeepLCreationForm(request.POST)
        if form.is_valid():
            lang_deepl=form.save()
            messages.success(request, _("La langue {} a été modifiée.").format(lang_deepl.lang_deepl))
            return redirect('langue_deepl_list')
        context = {'form':form, 'title':_("Modifier une langue prise en charge par Deepl")}
        return render(request, 'core/langue_deepl_form.html', context)

###################################################################################################

# Vue Création d'une raison de non réalisation de l'expérience

class No_showCreationView(View):
    def get(self, request, *args, **kwargs):
        form = No_showCreationForm()
        context = {'form': form, 'title':_("Créer une raison de non réalisation")}
        return render(request, 'core/no_show_form.html', context)
    
    def post(self, request, *args, **kwargs):
        form = No_showCreationForm(request.POST)
        if form.is_valid():
            no_show=form.save()
            translation_content.delay("core","No_show", no_show.id,"raison_noshow")
            messages.success(request, _("La raison de non réalisation {} a été créée.").format(no_show.raison_noshow))
            return redirect('no_show_list')
###################################################################################################

# Vue Liste des raisons de non réalisation de l'expérience

class No_showListView(View):
    def get(self, request, *args, **kwargs):
        no_shows = No_show.objects.all().order_by('raison_noshow')
        return render(request, 'core/no_show_list.html', {'no_shows': no_shows})
###################################################################################################

# Vue Modification d'une raison de non-réalisation de l'expérience

class No_showUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        no_show = get_object_or_404(No_show, pk=pk)
        form = No_showCreationForm(instance=no_show)
        context = {'form': form, 'title':_("Modifier une raison de non réalisation")}
        return render(request, 'core/no_show_form.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        no_show = get_object_or_404(No_show, pk=pk) 
        form = No_showCreationForm(request.POST)
        if form.is_valid():
            no_show=form.save()
            translation_content.delay("core","No_show", no_show.id,"raison_noshow")
            messages.success(request, _("La raison de non réalisation {} a été modifiée.").format(no_show.raison_noshow))
            return redirect('no_show_list')
###################################################################################################

# Vue Création d'un bénéficiaire des dons

class BeneficiaireCreationView(View):
    def get(self, request, *args, **kwargs):
        form = BeneficiaireCreationForm()
        context = {'form': form, 'title':_("Créer un bénéficiaire")}
        return render(request, 'core/beneficiaire_form.html', context)
    
    def post(self, request, *args, **kwargs):
        form = BeneficiaireCreationForm(request.POST)
        if form.is_valid:
            beneficiaire=form.save()
            translation_content.delay("core","Beneficiaire", beneficiaire.id,"nom_beneficiaire")
            messages.success(request, _("Le bénéficiaire {} a été créé.").format(beneficiaire.nom_beneficiaire))
            return redirect('beneficiaire_list')
###################################################################################################

# Vue Modification d'un bénéficiaire des dons

class BeneficiaireUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        beneficiaire = get_object_or_404(Beneficiaire, pk=pk)
        form = BeneficiaireCreationForm(instance=beneficiaire)
        context = {'form': form, 'title':_("Modifier un bénéficiaire")}
        return render(request, 'core/beneficiaire_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        beneficiaire = get_object_or_404(Beneficiaire, pk=pk)
        form = BeneficiaireCreationForm(request.POST)
        if form.is_valid():
            beneficiaire=form.save()
            translation_content.delay("core","Beneficiaire", beneficiaire.id,"nom_beneficiaire")
            messages.success(request, _("Le bénéficiaire {} a été modifié.").format(beneficiaire.nom_beneficiaire))
            return redirect('beneficiaire_list')
###################################################################################################

# Vue Liste des bénéficiaires des dons

class BeneficiaireListView(View):
    def get(self, request, *args, **kwargs):
        beneficiaires = Beneficiaire.objects.all().order_by('nom_beneficiaire')
        return render(request, 'core/beneficiaire_list.html', {'beneficiaires': beneficiaires})
###################################################################################################

# Vue Création d'une période de la journée    

class PeriodeCreationView(View):
    def get(self, request, *args, **kwargs):
        form = PeriodeCreationForm()
        context = {'form': form, 'title':_("Créer une période de la journée")}
        return render(request, 'core/periode_form.html', context)   
    
    def post(self, request, *args, **kwargs):
        form = PeriodeCreationForm(request.POST)
        if form.is_valid():
            periode=form.save()
            translation_content.delay("core","Periode", periode.id,"periode_journee")
            messages.success(request, _("La pé'periode_createriode de la journée {} a été créée.").format(periode.periode_journee))    
            return redirect('periode_list')
###################################################################################################

#Vue Liste des périodes de la journée

class PeriodeListView(View):
    def get(self, request, *args, **kwargs):
        periodes = Periode.objects.all().order_by('periode_journee')
        return render(request, 'core/periode_list.html', {'periodes': periodes})    
###################################################################################################

#Vue Modification d'une période de la journée

class PeriodeUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        periode = get_object_or_404(Periode, pk=pk)
        form = PeriodeCreationForm(instance=periode)
        context = {'form': form, 'title':_("Modifier une période de la journée")}
        return render(request, 'core/periode_form.html', context)   
    
    def post(self, request, pk, *args, **kwargs):   
        form=PeriodeCreationForm(request.POST)
        if form.is_valid():
            periode=form.save()
            translation_content.delay("core","Periode", periode.id,"periode_journee")
            messages.success(request, _("La période de la journée {} a été modifiée.").format(periode.periode_journee))
            return redirect('periode_list')
###################################################################################################

# Vue Création d'une tranche d'âge

class TrancheAgeCreationView(View):
    def get(self, request, *args, **kwargs):
        form = TrancheAgeCreationForm()
        context = {'form': form, 'title':_("Créer une tranche d'âge")}
        return render (request, 'core/tranche_age_form.html', context)
    
    def post(self, request, *args, **kwargs):
        form = TrancheAgeCreationForm(request.POST)
        if form.is_valid():
            tranche_age=form.save()
            translation_content.delay("core","TrancheAge", tranche_age.id,"tranche_age")
            messages.success(request, _("La tranche d'âge {} a été créée.").format(tranche_age.tranche_age))
            return redirect ('tranche_age_list')
###################################################################################################

# Vue Liste des tranches d'âges

class TrancheAgeListView(View):
    def get(self, request, *args, **kwargs):
        tranche_ages = TrancheAge.objects.all().order_by('tranche_age')
        return render(request, 'core/tranche_age_list.html', {'tranche_ages': tranche_ages})
###################################################################################################

# Vue Modification d'une tranche d'âge

class TrancheAgeUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        tranche_age = get_object_or_404(TrancheAge, pk=pk)
        form = TrancheAgeCreationForm(instance=tranche_age)
        context = {'form': form, 'title':_("Modifier une tranche d'âge")}
        return render(request, 'core/tranche_age_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        tranche_age = get_object_or_404(TrancheAge, pk=pk)
        form = TrancheAgeCreationForm(request.POST)
        if form.is_valid():
            tranche_age=form.save()
            translation_content.delay("core","TrancheAge", tranche_age.id,"tranche_age")
            messages.success(request, _("La tranche d'âge {} a été modifiée.").format(tranche_age.tranche))
            return redirect ('tranche_age_list')
###################################################################################################

# Vue Création d'un type de handicap

class Types_handicapCreationView(View):
    def get(self, request, *args, **kwargs):
        form = Types_handicapCreationForm()
        context = {'form': form, 'title':_("Créer un type de handicap")}
        return render(request, 'core/types_handicap_form.html', context)
    
    def post(self, request, *args, **kwargs):
        form = Types_handicapCreationForm(request.POST  )
        if form.is_valid():
            type_handicap=form.save()
            translation_content.delay("core","Types_handicap", type_handicap.id,"type_handicap")
            messages.success(request, _("Le type de handicap {} a été créé.").format(type_handicap.type_handicap))
            return redirect('types_handicap_list')
###################################################################################################

# Vue Liste des types de handicap

class Types_handicapListView(View):
    def get(self, request, *args, **kwargs):
        types_handicap = Types_handicap.objects.all().order_by('type_handicap')
        return render(request, 'core/types_handicap_list.html', {'types_handicap': types_handicap}) 
###################################################################################################

# Vue Modification d'un type de handicap 

class Types_handicapUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        type_handicap = get_object_or_404(Types_handicap, pk=pk)
        form = Types_handicapCreationForm(instance=type_handicap)
        context = {'form': form, 'title':_("Modifier un type de handicap")} 
        return render(request, 'core/types_handicap_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        type_handicap = get_object_or_404(Types_handicap, pk=pk)
        form = Types_handicapCreationForm(request.POST)
        if form.is_valid():
            type_handicap=form.save()
            translation_content.delay("core","Types_handicap", type_handicap.id,"type_handicap")
            messages.success(request, _("Le type de handicap {} a été modifié.").format(type_handicap.type_handicap))   
            return redirect('types_handicap_list')
###################################################################################################                                                                                     
                                                                        

# Vue AjaxCréation d'un utilisateur


import json
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

# On utilise csrf_protect au lieu de csrf_exempt pour la sécurité

class CreateUserView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            User = get_user_model()

            # 1. Validation des champs obligatoires
            required_fields = ['email', 'first_name', 'last_name']
            if not all(data.get(field) for field in required_fields):
                return JsonResponse({
                    'erreur': _("Les champs email, prénom et nom sont obligatoires.")
                }, status=400)

            # 2. Vérification de l'existence
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'erreur': _("Un utilisateur avec cet email existe déjà.")
                }, status=400)

            # 3. Préparation des ForeignKeys (Clés étrangères)
            # IMPORTANT : Si le code est vide, on doit passer None et non ''
            from cluster.models import Cluster
            from destination.models import Destination

            cluster_id = data.get('code_cluster')
            dest_id = data.get('code_dest')

            # On cherche les instances si les IDs sont fournis (cas d'une mise à jour)
            # Dans le cas d'une création de Cluster, ces variables resteront None
            cluster_obj = Cluster.objects.filter(id=cluster_id).first() if cluster_id else None
            dest_obj = Destination.objects.filter(id=dest_id).first() if dest_id else None

            # 4. Création de l'utilisateur
            user = User.objects.create(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                cellphone=data.get('cellphone', ''),
                lang_com=data.get('lang_com', 'fr'),
                code_cluster=cluster_obj, # Instance ou None
                code_dest=dest_obj,       # Instance ou None
                is_active=False           # Approche Draft : inactif par défaut
            )

            # Optionnel : Ne pas envoyer l'email tout de suite si l'utilisateur est inactif
            # ou si le cluster n'est pas encore totalement créé.
            # envoyer_email_creation_utilisateur(user, request)

            return JsonResponse({
                'id': user.id,
                'text': f"{user.first_name} {user.last_name}"
            })

        except json.JSONDecodeError:
            return JsonResponse({'erreur': _("Données JSON invalides.")}, status=400)
        except Exception as e:
            # Log de l'erreur réelle pour le développeur
            print(f"Erreur création user: {str(e)}")
            return JsonResponse({'erreur': _("Une erreur est survenue lors de la création.")}, status=500)

###################################################################################################
 # Vue Récupérer les langues de communication

def get_languages(request):
    languages = Language_communication.objects.all().values('code', 'name')
    return JsonResponse(list(languages), safe=False)

###################################################################################################
 #Vue pour récuperer les utilisateurs créés dans les clusters ou destinations

import json
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from destination.models import Destination

User = get_user_model()

class AjaxUserHandlerView(View):
    def get(self, request, *args, **kwargs):
        """Filtrage des utilisateurs selon le contexte Cluster/Dest."""
        cluster_code = request.GET.get('code_cluster')
        code_dest = request.GET.get('code_dest')
        
        # On récupère le type de formulaire si envoyé, sinon on le déduit
        # Si code_dest est présent, on considère qu'on est en mode "destination"
        is_dest_mode = bool(code_dest)

        # 1. Base : Inclure systématiquement les utilisateurs "Pending" (inactifs)
        # pour qu'ils apparaissent dès qu'ils sont créés via la modale
        query = Q(is_active=False)
        
        # 2. Gestion des utilisateurs actifs selon le périmètre
        if cluster_code:
            if is_dest_mode:
                # LOGIQUE STRICTE DESTINATION :
                # On veut les actifs qui ont EXACTEMENT ce cluster ET cette destination
                # On exclut ceux qui ont une destination vide ou nulle
                active_filter = Q(
                    is_active=True, 
                    code_cluster__code_cluster=cluster_code,
                    code_dest__code_dest=code_dest
                )
                
                # Optionnel : Gestion de l'héritage (Parent) si nécessaire
                dest_obj = Destination.objects.filter(code_dest=code_dest).first()
                if dest_obj and dest_obj.code_parent_dest:
                    active_filter |= Q(
                        is_active=True,
                        code_cluster__code_cluster=cluster_code,
                        code_dest__code_dest=dest_obj.code_parent_dest.code_dest
                    )
            else:
                # LOGIQUE CLUSTER (Si pas de code_dest fourni) :
                # On prend les actifs du cluster qui n'ont PAS de destination
                active_filter = Q(
                    is_active=True, 
                    code_cluster__code_cluster=cluster_code
                ) & (Q(code_dest__isnull=True) | Q(code_dest__code_dest=''))
            
            query |= active_filter

        # Exécution de la requête
        users = User.objects.filter(query).distinct().order_by('first_name', 'last_name')
        
        results = [{
            "id": user.id, 
            "text": f"{user.first_name} {user.last_name} ({_('Actif') if user.is_active else _('En attente')})",
            "is_active": user.is_active
        } for user in users]
        
        return JsonResponse(results, safe=False)

    def post(self, request, *args, **kwargs):
        """Création d'un utilisateur 'Pending'."""
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if User.objects.filter(email=email).exists():
                return JsonResponse({"erreur": _("Cet email est déjà utilisé.")}, status=400)

            user = User.objects.create(
                email=email,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                cellphone=data.get('cellphone', ''),
                lang_com=data.get('lang_com', 'fr'),
                is_active=False 
            )

            return JsonResponse({
                "id": user.id,
                "text": f"{user.first_name} {user.last_name}"
            }, status=201)
        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=400)

###################################################################################################

