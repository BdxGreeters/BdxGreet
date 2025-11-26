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
    
    code_cluster = forms.ModelChoiceField(
        queryset=Cluster.objects.all(), # Ou le queryset pertinent
        # ⭐ LA CLÉ : utilise le champ 'code' du Cluster comme valeur dans le HTML
        to_field_name='code_cluster',
        required=True,)

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
            'code_cluster': forms.Select(),
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

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

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
       

        self.helper = FormHelper()
        self.helper.form_method = 'post'
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
###################################################################################################

# Form des datas de la destination

class DestinationDataForm(HelpTextTooltipMixin, forms.ModelForm):

    class Meta:
        model = Destination_data
        fields = [
            'code_dest_data',
            'beneficiaire_don_dest',
            'donation_proposal_dest',
            'paypal_dest',
            'donation_text_dest',
            'tripadvisor_dest',
            'googlemybusiness_dest',
            'langs_com_dest',
            'lang_default_dest',
            'langs_parlee_dest',
            'Flag_modalités_dest',
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    _("Dons et langues de communication"),
                    Row(
                        Column('beneficiaire_don_dest', css_class='col-md-3'),
                        Column('donation_proposal_dest', css_class='col-md-3'),
                        Column('paypal_dest', css_class='col-md-3'),
                    ),                        
                    Row(
                        Column('donation_text_dest', css_class='col-md-12'),
                    ),
                ),
            ),
            Submit('submit', _('Enregistrer')),
        )

###################################################################################################

#Form des flux de la destination

class DestinationFluxForm(HelpTextTooltipMixin,forms.ModelForm):

    class Meta:
        model = Destination_flux
        fields = [
            'code_dest_flux',
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
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    _("Flux avant la balade"),
                    Row(
                        Column('frequence_mail_precoce', css_class='col-md-3'),
                        Column('confrmation_date_precoce_dest', css_class='col-md-3'),
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
                        Column('flus_saisie_suivie_dest', css_class='col-md-3'),
                    ),
                ),
            ),
            Submit('submit', _('Enregistrer')),
        )