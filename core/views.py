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
                        InterestCenterCreationForm, LangueDeepLCreationForm,
                        No_showCreationForm, PeriodeCreationForm,
                        TrancheAgeCreationForm, Types_handicapCreationForm)
from core.models import (Beneficiaire, Email_Mailjet, InterestCenter,
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

#Vue Création d'un centre d'intérêt et traduction dans les langues de communication
class InterestCenterCreationView(View):
    def get(self, request, *args, **kwargs):
        form = InterestCenterCreationForm()
        context = {'form': form, 'title':_("Créer un centre d'intérêt")}
        return render(request, 'core/interest_center_form.html', context)   
    
    def post(self,request, *args, **kwargs):
        form = InterestCenterCreationForm(request.POST)
        if form.is_valid():
            interest_center=form.save()
            translation_content.delay("core","InterestCenter", interest_center.id,"interest_center")
            messages.success(request, _("Le centre d'intérêt {} a été créé.").format(interest_center.interest_center))
            return redirect('interest_center_list')
        context = {'form': form, 'title':_("Créer un centre d'intérêt")}
        return render (request, 'core/interest_center_form.html', context)
###################################################################################################

# Vue Liste des centres d'intérêts

class InterestCenterListView(View):
    def get(self, request, *args, **kwargs):
        interest_centers = InterestCenter.objects.all().order_by('interest_center')
        return render(request, 'core/interest_center_list.html', {'interest_centers': interest_centers})    
###################################################################################################

# Vue modification d'un centre d'intérêt
class InterestCenterUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        interest_center = get_object_or_404(InterestCenter, pk=pk)
        form = InterestCenterCreationForm(instance=interest_center)
        context = {'form': form, 'title':_("Modifier un centre d'intérêt")} 
        return render(request, 'core/interest_center_form.html', context)


    def post(self, request, pk, *args, **kwargs):
        interest_center = get_object_or_404(InterestCenter, pk=pk)
        form = InterestCenterCreationForm(request.POST)
        if form.is_valid():
            interest_center=form.save()
            translation_content.delay("core","InterestCenter", interest_center.id,"interest_center")
            messages.success(request, _("Le centre d'intérêt {} a été modifié.").format(interest_center.interest_center))  
        context = {'form': form, 'title':_("Modifier un centre d'intérêt")}
        return render (request, 'core/interest_center_form.html', context)
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
                                                                        

# Vue Création d'un utilisateur


@method_decorator(csrf_exempt, name='dispatch')
class CreateUserView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            User = get_user_model()

            # Validation basique
            if not all(key in data for key in ['email', 'first_name', 'last_name']):
                raise ValidationError(_("Les champs email, first_name et last_name sont obligatoires."))

            if User.objects.filter(email=data['email']).exists():
                raise ValidationError(_("Un utilisateur avec cet email existe déjà."))
            

            print( data)
            print("data code_cluster:", data.get('code_cluster', ''))
            print("data code_dest:", data.get('code_dest', ''))
            user = User.objects.create(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                cellphone=data.get('cellphone', ''),
                lang_com=data.get('lang_com', 'fr'),
                code_cluster=data.get('code_cluster', ''),
                code_dest=data.get('code_dest', ''),
            )

            envoyer_email_creation_utilisateur(user, request)

            return JsonResponse({
                'id': user.id,
                'text': f"{user.first_name} {user.last_name}"
            })
        except ValidationError as e:
            return JsonResponse({
                'erreur': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'erreur': "Une erreur est survenue."
            }, status=500)

###################################################################################################
 # Vue Récupérer les langues de communication

def get_languages(request):
    languages = Language_communication.objects.all().values('code', 'name')
    return JsonResponse(list(languages), safe=False)

###################################################################################################
 #Vue pour récuperer les utilisateurs existants pour les champs FK dans le formulaire de destination

User = get_user_model()

def get_users_json(request):
    code_cluster = request.GET.get('code_cluster', None)
    code_dest = request.GET.get('code_dest', None)
    print("code_cluster:", code_cluster)
    print("code_dest:", code_dest)    
    # Filtrer les utilisateurs en fonction des paramètres
    users = User.objects.all().order_by('last_name', 'first_name')

    # Appliquer les filtres si les paramètres sont présents
    if code_cluster:
        # Filtrer les utilisateurs liés à un cluster spécifique
        users = users.filter(code_cluster=code_cluster)
    if code_dest:
        # Filtrer les utilisateurs liés à une destination spécifique
        users = users.filter(code_dest=code_dest)


    # Préparer les données pour la réponse JSON
    users_data = users.values('id', 'first_name', 'last_name')

    return JsonResponse(list(users_data), safe=False)

###################################################################################################
