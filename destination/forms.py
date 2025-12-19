from crispy_forms.bootstrap import (InlineCheckboxes, InlineRadios, Tab,
                                    TabHolder)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, Column, Div, Field, Fieldset, Hidden,
                                 Layout, Row, Submit)
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from cluster.models import Cluster
from core.mixins import CommaSeparatedFieldMixin, HelpTextTooltipMixin
from core.models import FieldPermission, Language_communication, Pays
from destination.models import Destination, Destination_data, Destination_flux

User = get_user_model()

class DestinationForm(HelpTextTooltipMixin, CommaSeparatedFieldMixin, forms.ModelForm):

    # Champs modifiables par le matcher
    matcher_fields = [
        'list_places_dest',
        'mini_lp_dest',
        'max_lp_dest',
        'mini_interest_center_dest',
        'max_interest_center_dest',
        'flag_stay_dest',
        'dispersion_param_dest'
        ]

    # Champ pour sélectionner le cluster par son code quand un user a un cluster attribué
    code_cluster = forms.ModelChoiceField(
        queryset=Cluster.objects.all(), # Ou le queryset pertinent
        # ⭐ LA CLÉ : utilise le champ 'code' du Cluster comme valeur dans le HTML
        to_field_name='code_cluster',
        required=True,)
    code_cluster_hidden = forms.CharField(widget=forms.HiddenInput(), required=False)   

    class Meta:
        model = Destination
        fields = [
            'code_cluster',
            'code_dest',
            'name_dest',
            'code_parent_dest',
            'code_IGA_dest',
            'desc_dest',
            'statut_dest',
            'adress_dest',
            'region_dest',
            'country_dest',
            'logo_dest',
            'libelle_email_dest',
            'URL_retry_dest',
            'mail_notification_dest',
            'mail_response_dest',
            'manager_dest',
            'referent_dest',
            'matcher_dest',
            'matcher_alt_dest',
            'finance_dest',
            'list_places_dest',
            'mini_lp_dest',
            'max_lp_dest',
            'mini_interest_center_dest',
            'max_interest_center_dest',
            'flag_stay_dest',
            'dispersion_param_dest',
            'disability_dest',
            'disability_libelle_dest',

        ]
        widgets = {
            'status_dest': forms.RadioSelect(),
            'code_cluster': forms.Select(attrs={'class': 'form-select'}),
            'pays_dest': forms.Select(),
            'statut_dest': forms.RadioSelect(),
            'desc_dest': forms.Textarea(attrs={'rows': 2}),
            'adress_dest': forms.Textarea(attrs={'rows': 2}),
            'list_places_dest': forms.TextInput(attrs={'class': '.comma-input-field'}),
            'disability_libelle_dest': forms.Textarea(attrs={'rows': 3}),
        }

    comma_fields_config = {
        'list_places_dest': {'min':2, 'max':10},
        }

    def __init__(self, *args,code_cluster_user=None, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        user=kwargs.pop('user', None)
        self.is_update=kwargs.pop('is_update', False)
        
        super().__init__(*args, **kwargs)

        # Si on est en mode mise à jour et que l'instance a un cluster, pré-remplir et désactiver le champ code_cluster
        if self.is_update and self.instance and self.instance.code_cluster:
            self.initial['code_cluster'] = self.instance.code_cluster.code_cluster
            self.fields['code_cluster'].disabled = True # Désactiver le champ pour empêcher la modification
            self.fields['code_dest'].disabled = True # Désactiver le champ pour empêcher la modification      
        else:
        # Si un code_cluster_user est fourni, filtrer les clusters disponibles
            if code_cluster_user:
                self.fields['code_cluster'].queryset = Cluster.objects.filter(code_cluster=code_cluster_user)
                self.fields['code_cluster'].initial = get_object_or_404(Cluster, code_cluster=code_cluster_user)
                self.fields['code_cluster'].disabled = True # Désactiver le champ pour empêcher la modification

        # Récupérer les codes des destinations existantes, sauf celle en cours d'édition
        existing_destinations = Destination.objects.exclude(
        pk=self.instance.pk  # Exclure la destination en cours d'édition
        ).values_list('code_dest', flat=True)

        # Créer une liste de choix pour le champ code_parent_dest
        choices = [(code, code) for code in existing_destinations]
        # Ajouter une option vide pour permettre de ne pas choisir de parent
        choices.insert(0, ('', '---------'))

        # Mettre à jour le champ code_parent_dest
        self.fields['code_parent_dest'] = forms.ChoiceField(
        choices=choices,
        required=False,
        label="Code Parent",
        )

        # Lister les utilisateurs par ordre alphabétique membres de  la destination en cours d'édition
        user_queryset = User.objects.all().order_by('last_name', 'first_name')
        self.fields['manager_dest'].queryset = user_queryset
        self.fields['referent_dest'].queryset = user_queryset
        self.fields['matcher_dest'].queryset = user_queryset
        self.fields['matcher_alt_dest'].queryset = user_queryset
        self.fields['finance_dest'].queryset = user_queryset
       

        
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    _("Informations générales"),
                    Row(
                        Column('code_cluster', css_class='col-md-2 col-lg-2'),
                        Column('code_dest', css_class='col-md-2'),
                        Column('name_dest', css_class='col-md-4'),
                        Column('code_parent_dest', css_class='col-md-2'),
                        Column('code_IGA_dest', css_class='col-md-2'),
                    ),
                    Row (
                        Column(InlineCheckboxes('statut_dest', css_class='col-md-12')),
                    ),
                    Row(        
                        Column('desc_dest', css_class='col-md-12'),
                    ),
                    Row(
                        Column('adress_dest', css_class='col-md-4'),
                        Column('region_dest', css_class='col-md-4'),
                        Column('country_dest', css_class='col-md-4'),
                    ),
                    Row(
                        Column('logo_dest', css_class='col-md-4'),
                        Column('libelle_email_dest', css_class='col-md-4'),
                        Column('URL_retry_dest', css_class='col-md-4'),
                    ),
                    Row(
                        Column('mail_notification_dest', css_class='col-md-6'),
                        Column('mail_response_dest', css_class='col-md-6'),
                    ),          
                    
                    ),
                Tab(
                    _("Administration"),
                    Row(
                        Column('manager_dest', css_class='col-md-6'),
                        Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_manager_dest">{_("Nouvel utilisateur")}</button>'),
                        css_class="d-flex align-items-center")
                    ),
                    Row(
                        Column('referent_dest', css_class='col-md-6'),
                        Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_referent_dest">{_("Nouvel utilisateur")}</button>'),
                        css_class="d-flex align-items-center")
                    ),
                    Row(
                        Column('matcher_dest', css_class='col-md-6'),
                        Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_matcher_dest">{_("Nouvel utilisateur")}</button>'),
                        css_class="d-flex align-items-center")
                    ),
                    Row(
                        Column('matcher_alt_dest', css_class='col-md-6'),
                        Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_matcher_alt_dest">{_("Nouvel utilisateur")}</button>'),
                               css_class="d-flex align-items-center")
                    ),
                    Row(
                        Column('finance_dest', css_class='col-md-6'),
                        Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_finance_dest">{_("Nouvel utilisateur")}</button>'),
                               css_class="d-flex align-items-center")
                    ),
                    ),
                Tab(
                    _("Lieux, centres d'intérêts,dates de séjour et accessibilité"),
                    Row(
                        Column('list_places_dest', css_class='col-md-12'),
                    ),
                    Row(
                        Column('mini_lp_dest', css_class='col-md-3'),
                        Column('max_lp_dest', css_class='col-md-3'),
                        ),
                    Row(
                        Column('mini_interest_center_dest', css_class='col-md-3'),
                        Column('max_interest_center_dest', css_class='col-md-3'),
                        ),
                    Row(    
                        Column('flag_stay_dest', css_class='col-md-3'),
                        Column('dispersion_param_dest', css_class='col-md-3'),
                    ),
                    Row(
                        Column('disability_dest', css_class='col-md-2'),
                        Column('disability_libelle_dest', css_class='col-md-10'),
                    ),
                ),
            ),
            Submit('submit', _('Enregistrer')),
        )

    def clean(self):
        cleaned_data = super().clean()  

         #Vérification du nombre maximun de centres d'interêts sélectionnés

        # 1. Récupérer le cluster sélectionné
        cluster = cleaned_data.get('code_cluster')
        
        # 2. Récupérer la valeur de max_interest_center_dest
        max_interest_center_dest = cleaned_data.get('max_interest_center_dest')

        if cluster and max_interest_center_dest is not None:
            # 3. Calculer le nombre d'items dans profil_interet_cluster du cluster
            
            # Récupère la chaîne de centres d'intérêt
            interet_cluster_str = cluster.profil_interet_cluster
            
            # Sépare les items par la virgule et filtre les chaînes vides
            # Ex: "sport,lecture,musique" -> ['sport', 'lecture', 'musique'] -> 3
            # Ex: "sport,,lecture" -> ['sport', 'lecture'] -> 2
            list_interets = [
                item.strip() 
                for item in interet_cluster_str.split(',') 
                if item.strip()
            ]
            
            total_interets = len(list_interets)

            # 4. Effectuer la comparaison
            if max_interest_center_dest > total_interets:
                # Si la validation échoue, lever une ValidationError pour le champ
                msg = _(
                    "Le nombre maximum de centres d'intérêts (%(max_ci)s) ne peut pas être supérieur au nombre total de centres d'intérêts du cluster sélectionné (%(total_ci)s)."
                ) % {
                    'max_ci': max_interest_center_dest, 
                    'total_ci': total_interets
                }
                
                # Ajoute l'erreur au champ max_interest_center_dest
                self.add_error('max_interest_center_dest', msg)

        #Vérification du nombre maximun de lieux ou thèmes sélectionnés
        max_lp_dest = cleaned_data.get('max_lp_dest')
        list_places_dest = cleaned_data.get('list_places_dest')

        if list_places_dest and max_lp_dest is not None:
            # Sépare les lieux par la virgule et filtre les chaînes vides
            list_lieux = [
                item.strip() 
                for item in list_places_dest.split(',') 
                if item.strip()
            ]
            
            total_lieux = len(list_lieux)

            # Effectuer la comparaison
            if max_lp_dest > total_lieux:
                # Si la validation échoue, lever une ValidationError pour le champ
                msg = _(
                    "Le nombre maximum de lieux ou thèmes (%(max_lp)s) ne peut pas être supérieur au nombre total de lieux ou thèmes sélectionnés (%(total_lp)s)."
                ) % {
                    'max_lp': max_lp_dest, 
                    'total_lp': total_lieux
                }
                
                # Ajoute l'erreur au champ max_lp_dest
                self.add_error('max_lp_dest', msg)  
        
        # Vérification que les max sont supérieurs ou égaux aux min
        mini_interest_center_dest = cleaned_data.get('mini_interest_center_dest')
        mini_lp_dest = cleaned_data.get('mini_lp_dest')
        if (max_interest_center_dest is not None and mini_interest_center_dest is not None and max_interest_center_dest < mini_interest_center_dest):
            self.add_error('max_interest_center_dest', _("Le maximum de centres d'intérêt ne peut pas être inférieur au minimum."))     
        if (max_lp_dest is not None and mini_lp_dest is not None and max_lp_dest < mini_lp_dest):
            self.add_error('max_lp_dest', _("Le maximum de lieux ou thèmes ne peut pas être inférieur au minimum."))
                
        return cleaned_data
    

###################################################################################################

# Form des datas de la destination

class DestinationDataForm(HelpTextTooltipMixin, forms.ModelForm):

    class Meta:
        model = Destination_data
        fields = [
            'beneficiaire_don_dest',
            'donation_proposal_dest',
            'paypal_dest',
            'donation_text_dest',
            'tripadvisor_dest',
            'googlemybusiness_dest',
            'langs_com_dest',
            'lang_default_dest',
            'langs_parlee_dest',
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
            'flag_NoAnswer_visitor_dest',
            'flag_reason_NoAnswer_greeter_dest',
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
            'date_fin_avis_mail_dest',
        ]
        widgets = {
            'beneficiaire_don_dest': forms.Select(),
            'donation_text_dest': forms.Textarea(attrs={'rows': 2}),
            'langs_com_dest': forms.SelectMultiple(),
            'langs_parlee_dest': forms.SelectMultiple(),
            'date_cg_mail_dest': forms.DateInput(attrs={'type': 'date'}),
            'date_début_avis_fermeture_dest': forms.DateInput(attrs={'type': 'date'}),
            'date_fin_avis_fermeture_dest': forms.DateInput(attrs={'type': 'date'}),
            'date_debut_avis_mail_dest': forms.DateInput(attrs={'type': 'date'}),
            'date_fin_avis_mail_dest': forms.DateInput(attrs={'type': 'date'}),
            'param_comment_visitor_dest': forms.Textarea(attrs={'rows': 2}),
            'flag_NoAnswer_visitor_dest': forms.RadioSelect(),
            'nbre_participants_fermeture_dest': forms.NumberInput,
            'texte_avis_fermeture_dest': forms.Textarea(attrs={'rows': 2}),
            'texte_avis_mail_dest': forms.Textarea(attrs={'rows': 2}),
        }

    
    def __init__(self, *args,  **kwargs):
        cluster_instance = kwargs.pop('cluster_instance', None)
        instance = kwargs.get('instance', None)
        cluster = None
        
        # Logique de récupération du cluster
        if instance and hasattr(instance, 'code_dest_data'):
            # instance est un Destination_data, on remonte vers Destination
            cluster = instance.code_dest_data.code_cluster
        elif cluster_instance:
            cluster = cluster_instance
        else:
            # Cas d'une création via initial data
            initial_data = kwargs.get('initial', {})
            destination_obj = initial_data.get('code_dest_data')
            if destination_obj:
                cluster = destination_obj.code_cluster

        super().__init__(*args, **kwargs)
        
        if cluster:
            cluster_langs_ids=cluster.langs_com.values_list('code', flat=True)
            self.fields['langs_com_dest'].queryset = Language_communication.objects.filter(code__in=cluster_langs_ids)
            self.fields['lang_default_dest'].queryset = Language_communication.objects.filter(code__in=cluster_langs_ids)
        else:
            self.fields['langs_com_dest'].queryset = Language_communication.objects.none()
            self.fields['lang_default_dest'].queryset = Language_communication.objects.none()        
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    _("Dons, langues de communication et réseaux sociaux"),
                    Row(
                        Column('beneficiaire_don_dest', css_class='col-md-3'),
                        Column('donation_proposal_dest', css_class='col-md-2'),
                        Column('paypal_dest', css_class='col-md-3'),
                        Column('donation_text_dest', css_class='col-md-4'),
                    ),                        
                    Row(
                        Column('tripadvisor_dest', css_class='col-md-4'),
                        Column('googlemybusiness_dest', css_class='col-md-4'),
                    ),
                    Row(
                        Column('lang_default_dest', css_class='col-md-3'),
                        Column('langs_com_dest', css_class='col-md-3'),
                        Column('langs_parlee_dest', css_class='col-md-3'),
                        ),
                ),
                Tab(
                    _("Gestion des demandes"),
                    Row(
                        Column('flag_modalités_dest',css_class='col-md-3'),
                        Column('date_cg_mail_dest',css_class='col-md-4'),
                        Column('periode_mail_cg_dest',css_class='col-md-4'),
                    ),
                    Row(
                        Column('flag_cg_T_dest',css_class='col-md-5'),
                        Column('flag_cg_U_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('flag_comment_visitor_dest',css_class='col-md-5'),
                        Column('param_comment_visitor_dest',css_class='col-md-5'),
                    ),
                   
                    Row(
                        Column('libelle_form_coche1_dest',css_class='col-md-5'),
                        Column('lib_url_form_coche1_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('url_form_coche1_dest', css_class='col-md-5'),
                        Column('flag_request_coche1_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('libelle_form_coche2_dest',css_class='col-md-5'),
                        Column('lib_url_form_coche2_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('url_form_coche2_dest', css_class='col-md-5'),
                        Column('flag_request_coche2_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('libelle_form_coche3_dest',css_class='col-md-5'),
                        Column('lib_url_form_coche3_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('url_form_coche3_dest', css_class='col-md-5'),
                        Column('flag_request_coche3_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('flag_NoAnswer_visitor_dest',css_class='col-md-5'),
                        Column('flag_reason_NoAnswer_greeter_dest',css_class='col-md-5'),
                    ),
                ),
                
                Tab(
                    _('Signature des courriels'),
                    Row(
                        Column('name_sign_mail_dest',css_class='col-md-5'),
                        Column('url_mail_signature_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('libelle_social1_mail_dest',css_class='col-md-5'),
                        Column('url_social1_mail_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('libelle_social2_mail_dest',css_class='col-md-5'),
                        Column('url_social2_mail_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('tagline_mail_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('titre_avis_mail_dest',css_class='col-md-5'),
                        Column('texte_avis_mail_dest',css_class='col-md-5'),
                    ),
                    Row(
                        Column('date_debut_avis_mail_dest',css_class='col-md-5'),
                        Column('date_fin_avis_mail_dest',css_class='col-md-5'),
                    ),
                ),
                Tab(
                    _('Avis de fermetures exceptionnelles    '),
                    Row(
                        Column('avis_fermeture_dest',css_class='col-md-5'),
                        Column('date_début_avis_fermeture_dest',css_class='col-md-3'),
                        Column('date_fin_avis_fermeture_dest',css_class='col-md-3'),
                    ),
                    Row(
                        Column('nbre_participants_fermeture_dest',css_class='col-md-5'),
                        Column('texte_avis_fermeture_dest',css_class='col-md-5'),
                    ),  
                ),
            ),
            Submit('submit', _("Enregistrer"), css_class='btn-primary'),        
        )
    def clean(self):
        
        cleaned_data = super().clean()

        # Récupération des dates de fermeture et de mail
        date_debut_avis_fermeture = cleaned_data.get("date_début_avis_fermeture_dest")
        date_fin_avis_fermeture = cleaned_data.get("date_fin_avis_fermeture_dest")

        date_debut_avis_mail = cleaned_data.get("date_debut_avis_mail_dest")
        date_fin_avis_mail = cleaned_data.get("date_fin_avis_mail_dest")

        # Vérification pour les dates de fermeture
        if date_debut_avis_fermeture and date_fin_avis_fermeture:
            if date_fin_avis_fermeture < date_debut_avis_fermeture:
                self.add_error("date_fin_avis_fermeture_dest", "La date de fin doit être postérieure à la date de début.")

        # Vérification pour les dates de mail
        if date_debut_avis_mail and date_fin_avis_mail:
            if date_fin_avis_mail < date_debut_avis_mail:
                self.add_error("date_fin_avis_mail_dest", "La date de fin doit être postérieure à la date de début.")
        
        # Vérification pour param_comment_visitor_dest si flag_comment_visitor_dest est coché
        flag_comment_visitor = cleaned_data.get("flag_comment_visitor_dest")
        param_comment_visitor = cleaned_data.get("param_comment_visitor_dest")

        if flag_comment_visitor and not param_comment_visitor:
            self.add_error("param_comment_visitor_dest", "Ce champ est obligatoire si le flag est coché.")
        
       
        return cleaned_data
    
###################################################################################################

#Form des flux de la destination

class DestinationFluxForm(HelpTextTooltipMixin,forms.ModelForm):

    class Meta:
        model = Destination_flux
        fields = [
            'frequence_mail_precoce',
            'confirmation_date_precoce_dest',
            'flux_treatement_dest',
            'flux_urgency_dest',
            'flux_delai_organisation_dest',
            'flux_delai_max_greeter_dest',
            'flux_frequence_relance_greeter_dest',
            'flux_delai_visiteur_max_dest',
            'flux_frequence_relance_visiteur_dest',
            'flux_delai_pre_balade_dest',
            'flux_saisie_suivie_dest',
            'flux_delai_compte_rendu_dest',
            'flux_frequence_compte_rendu_dest',
            'flux_delai_envoi_avis_dest',
            'flux_frequence_envoi_avis_dest',
            'flux_delai_avis_max_dest',
            'flux_rgpd_dest',       
        ]
    


    def __init__(self, *args, **kwargs):
        cluster_instance = kwargs.pop('cluster_instance', None)
        instance = kwargs.get('instance', None)
        cluster = None
        
        # Logique de récupération du cluster
        if instance and hasattr(instance, 'code_dest_data'):
            # instance est un Destination_flux, on remonte vers Destination
            cluster = instance.code_dest_flux.code_cluster
        elif cluster_instance:
            cluster = cluster_instance
        else:
            # Cas d'une création via initial data
            initial_data = kwargs.get('initial', {})
            destination_obj = initial_data.get('code_dest_flux')
            if destination_obj:
                cluster = destination_obj.code_cluster

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    _("Flux avant la balade"),
                    Row(
                        Column('frequence_mail_precoce', css_class='col-md-3'),
                        Column('confirmation_date_precoce_dest', css_class='col-md-3'),
                        Column('flux_treatement_dest', css_class='col-md-3'),
                    ),
                    Row(
                        Column('flux_urgency_dest', css_class='col-md-3'),
                        Column('flux_delai_organisation_dest', css_class='col-md-3'),
                        Column('flux_delai_max_greeter_dest', css_class='col-md-3'),
                    ),
                    Row(
                        Column('flux_frequence_relance_greeter_dest', css_class='col-md-3'),
                        Column('flux_delai_visiteur_max_dest', css_class='col-md-3'),
                        Column('flux_frequence_relance_visiteur_dest', css_class='col-md-3'),
                    ),
                    Row(
                        Column('flux_delai_pre_balade_dest', css_class='col-md-3'),
                        Column('flux_saisie_suivie_dest', css_class='col-md-3'),
                    ),
                ),
                Tab(
                    _('Compte-rendu de la balade'),
                    Row(
                        Column('flux_delai_compte_rendu_dest',css_class='col-md_3'),
                        Column('flux_frequence_compte_rendu_dest',css_class='col-md-3'),
                    ),
                    Row(
                        Column('flux_delai_envoi_avis_dest',css_class='col-md-4'),
                        Column('flux_frequence_envoi_avis_dest',css_class='col-md-4'),
                        Column('flux_delai_avis_max_dest',css_class='col-md-4'),
                    ),
                ),
                Tab(
                    _('Gestion des données personnelles'),
                    Row(
                        Column('flux_rgpd_dest',css_class='col-md-3'),
                    ),
                ),
            ),
            Submit('submit', _("Enregistrer"), css_class='btn-primary'), 
        )