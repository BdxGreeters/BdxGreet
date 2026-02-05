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
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from cluster.models import Cluster
from core.mixins import CommaSeparatedFieldMixin, HelpTextTooltipMixin
from core.models import FieldPermission, Language_communication, Pays
from destination.models import Destination, Destination_data, Destination_flux

from django.utils.safestring import mark_safe

class ImagePreviewWidget(forms.ClearableFileInput):
    def render(self, name, value, attrs=None, renderer=None):
        print(f"Rendering widget for {name} with value {value}")
        output = super().render(name, value, attrs, renderer)
        if value and hasattr(value, 'url'):
            preview_html = f'''
                <div class="mb-3">
                    <p style="margin-bottom: 5px; font-weight: bold;">Aperçu du logo :</p>
                    <img src="{value.url}" alt="Logo actuel" 
                         style="max-height: 120px; border: 2px solid #eee; border-radius: 8px; shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                </div>
            '''
            return mark_safe(preview_html + output)
        return output
    
User = get_user_model()

class DestinationForm(HelpTextTooltipMixin, CommaSeparatedFieldMixin, forms.ModelForm):
    # Champs cachés pour l'AJAX
    pending_manager_dest_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    pending_referent_dest_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    pending_matcher_dest_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    pending_matcher_alt_dest_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    pending_finance_dest_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    list_places_dest = forms.CharField(
        required=True, 
        label=_("Lieux ou thèmes"), 
        help_text=_("Saisissez les lieux ou thèmes en les validant par Entrée")
    )

    code_cluster = forms.ModelChoiceField(
        queryset=Cluster.objects.all(),
        to_field_name='code_cluster',
        required=True,
        label=_("Cluster")
    )

    class Meta:
        model = Destination
        fields = [
            'code_cluster', 'code_dest', 'name_dest', 'code_parent_dest',
            'code_IGA_dest', 'desc_dest', 'statut_dest', 'adress_dest',
            'region_dest', 'country_dest', 'logo_dest', 'libelle_email_dest',
            'URL_retry_dest', 'mail_notification_dest', 'mail_response_dest',
            'manager_dest', 'referent_dest', 'matcher_dest', 'matcher_alt_dest',
            'finance_dest', 'mini_lp_dest', 'max_lp_dest', 
            'mini_interest_center_dest', 'max_interest_center_dest',
            'flag_stay_dest', 'dispersion_param_dest', 'disability_dest',
            'disability_libelle_dest',
        ]
        widgets = {
            'statut_dest': forms.RadioSelect(),
            'desc_dest': forms.Textarea(attrs={'rows': 2}),
            'adress_dest': forms.Textarea(attrs={'rows': 2}),
            'disability_libelle_dest': forms.Textarea(attrs={'rows': 3}),
            'logo_dest': ImagePreviewWidget(),
        }

    comma_fields_config = {
        'list_places_dest': {'min': 2, 'max': 10},
    }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        code_cluster_user = kwargs.pop('code_cluster_user', None)
        is_update_arg= kwargs.pop('is_update', False)
        # Détection automatique du mode Update
        super().__init__(*args, **kwargs)
        self.fields['logo_dest'].widget = ImagePreviewWidget()
        self.is_updating = is_update_arg or (self.instance and self.instance.pk)    

        # 1. LOGIQUE CLUSTER & ÉDITION (Sécurisée)
        if self.is_updating:
            # Verrouillage des champs code_cluster et code_dest en édition
            if 'code_cluster' in self.fields:
                self.fields['code_cluster'].widget = forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
                self.initial['code_cluster'] = str(self.instance.code_cluster)
                self.fields['code_cluster'].disabled = True
                self.fields['code_cluster'].required = False

            if 'code_dest' in self.fields:
                self.fields['code_dest'].disabled = True
                self.fields['code_dest'].widget.attrs['readonly'] = True
        else:
            if code_cluster_user:
                qs = Cluster.objects.filter(code_cluster=code_cluster_user)
                self.fields['code_cluster'].queryset = qs
                if qs.exists():
                    self.fields['code_cluster'].initial = qs.first()
                self.fields['code_cluster'].disabled = True

        # 2. LOGIQUE CODE PARENT
        current_pk = self.instance.pk if self.is_updating else None
        existing_destinations = Destination.objects.exclude(pk=current_pk).values_list('code_dest', flat=True)
        self.fields['code_parent_dest'] = forms.ChoiceField(
            choices=[('', '---------')] + [(c, c) for c in existing_destinations],
            required=False, label=_("Code Parent"),
            widget=forms.Select(attrs={
            'data-ajax-url': reverse('get_parent_info'),
            'class': 'form-select' # ou 'form-control' selon votre version de Bootstrap
            })
        )

        # 3. LOGIQUE UTILISATEURS
        current_cluster = code_cluster_user
        if not current_cluster and self.is_updating and self.instance.code_cluster:
            current_cluster = self.instance.code_cluster.code_cluster

        user_qs = User.objects.all().order_by('last_name', 'first_name')
        if current_cluster:
            user_qs = user_qs.filter(Q(code_cluster__code_cluster=current_cluster) | Q(code_cluster__isnull=True))

        user_fields = ['manager_dest', 'referent_dest', 'matcher_dest', 'matcher_alt_dest', 'finance_dest']
        for field in user_fields:
            if field in self.fields:
                self.fields[field].queryset = user_qs
                self.fields[field].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}"
        # 4. CRISPY LAYOUT
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Hidden('pending_manager_dest_id', ''),
            Hidden('pending_referent_dest_id', ''),
            Hidden('pending_matcher_dest_id', ''),
            Hidden('pending_matcher_alt_dest_id', ''),
            Hidden('pending_finance_dest_id', ''),
            TabHolder(
                Tab(_("Informations générales"),
                    Row(
                        Column('code_cluster', css_class='col-md-2'),
                        Column('code_dest', css_class='col-md-2'),
                        Column('name_dest', css_class='col-md-4'),
                        Column('code_parent_dest', css_class='col-md-2'),
                        Column('code_IGA_dest', css_class='col-md-2'),
                    ),
                    Row(Column(InlineRadios('statut_dest', css_class='col-md-12'))),
                    Row(Column('desc_dest', css_class='col-md-12')),
                    Row(Column('adress_dest', css_class='col-md-4'), Column('region_dest', css_class='col-md-4'), Column('country_dest', css_class='col-md-4')),
                    Row(Column('logo_dest', css_class='col-md-4'), Column('libelle_email_dest', css_class='col-md-4'), Column('URL_retry_dest', css_class='col-md-4')),
                    Row(Column('mail_notification_dest', css_class='col-md-6'), Column('mail_response_dest', css_class='col-md-6')),
                ),
                Tab(_("Administration"),
                    *[Row(
                        Column(f, css_class='col-md-8'),
                        Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_{f}"><i class="fas fa-plus"></i>{_("Nouvel utilisateur")}</button>'), css_class='col-md-4')
                    ) for f in user_fields]
                ),
                Tab(_("Lieux & Paramètres"),
                    Row(Column('list_places_dest', css_class='col-md-12')),
                    Row(Column('mini_lp_dest', css_class='col-md-3'), Column('max_lp_dest', css_class='col-md-3')),
                    Row(Column('mini_interest_center_dest', css_class='col-md-3'), Column('max_interest_center_dest', css_class='col-md-3')),
                    Row(Column('flag_stay_dest', css_class='col-md-3'), Column('dispersion_param_dest', css_class='col-md-3')),
                    Row(Column('disability_dest', css_class='col-md-2'), Column('disability_libelle_dest', css_class='col-md-10')),
                ),
            ),
            Submit('submit', _('Enregistrer'), css_class='btn-primary mt-3'),
        )

        if hasattr(self, 'apply_tooltips'):
            self.apply_tooltips()

    def clean(self):
        cd = super().clean()
        
        # Validation Centres d'intérêt
        cluster = cd.get('code_cluster')
        mx_ic, mi_ic = cd.get('max_interest_center_dest'), cd.get('mini_interest_center_dest')
        
        if cluster and mx_ic:
            total_ic = cluster.interest_center.count()
            if mx_ic > total_ic:
                self.add_error('max_interest_center_dest', _("Max ({}) > Total cluster ({})").format(mx_ic, total_ic))
        
        if mx_ic and mi_ic and mx_ic < mi_ic:
            self.add_error('max_interest_center_dest', _("Le maximum doit être supérieur au minimum."))

        # Validation Lieux (list_places_dest)
        mx_lp, mi_lp = cd.get('max_lp_dest'), cd.get('mini_lp_dest')
        list_p = cd.get('list_places_dest', '')
        
        if list_p and mx_lp:
            count_p = len([p for p in list_p.split(',') if p.strip()])
            if mx_lp > count_p:
                self.add_error('max_lp_dest', _("Max ({}) > Nombre de lieux saisis ({})").format(mx_lp, count_p))

        return cd


    

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
        
        self.apply_tooltips() #Appel du mixin HelpextTooltip


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

        self.apply_tooltips() #Appel du mixin HelpextTooltip

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