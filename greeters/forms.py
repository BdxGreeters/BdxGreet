from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from crispy_forms.bootstrap import (InlineCheckboxes, InlineRadios, Tab,
                                    TabHolder)
from users.models import CustomUser
from greeters.models import Greeter, GreeterType, Indisponibility
from crispy_forms.bootstrap import (InlineCheckboxes, InlineRadios, Tab,
                                    TabHolder)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, Column, Div, Field, Fieldset, Hidden,
                                 Layout, Row, Submit)
from django import forms
from django.contrib.auth import get_user_model
from core.mixins import CommaSeparatedFieldMixin, HelpTextTooltipMixin
from crispy_forms.bootstrap import TabHolder, Tab
from cluster.models import Cluster
from destination.models import Destination
User=get_user_model()

class GreeterCombinedForm(HelpTextTooltipMixin, forms.ModelForm):
    # On définit ici les champs de CustomUser que l'on veut ajouter au formulaire Greeter
    email = forms.EmailField(label=_("Email"),help_text=_("Saisir l'adresse courriel du Greeter"))
    first_name = forms.CharField(label=_("Prénom"), help_text=_("Saisir le prénom du Greeter"))
    last_name = forms.CharField(label=_("Nom"), help_text=_("Saisir le nom du Greeter"))
    cellphone = forms.CharField(label=_("Téléphone Mobile"), help_text=_("Saisir le numéro de téléphone mobile du Greeter"))
    lang_com = lang_com = forms.ChoiceField(
        label=_("Langue de communication"),
        choices=settings.LANGUAGES, 
        initial=settings.LANGUAGE_CODE,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Saisir la langue de communication du Greeter")
        )
    cluster = forms.ModelChoiceField(
            queryset=Cluster.objects.all(),
            widget=forms.Select(attrs={'class': 'form-control'}),
            help_text=_("Sélectionner le cluster associé au Greeter")
            )   
    destination = forms.ModelChoiceField(
            queryset=Destination.objects.all(),
            widget=forms.Select(attrs={'class': 'form-control'}),
            help_text=_("Sélectionner la destination associée au Greeter")
            )


    class Meta:
        model = Greeter
        fields = (
            'statut_greeter',
            'genre_greeter',
            'age_greeter',
            'adress1_greeter',
            'adress2_greeter',
            'postalcode_greeter',
            'city_greeter',
            'country_greeter',
            'landline_phone_greeter',
            'whatsapp_phone_greeter',
            'experiences_greeters',
            'photo',
            'bio_greeter',
            'handicap_greeter',
            'visibily_greeter',
            'langues_parlées_greeter',
            'max_participants_greeter',
            'disponibility_day_greeter',
            'disponibility_time_greeter',
            'frequency_greeter',
            'comments_greeter',
            'interest_greeter',
            'list_places_greeter',
            'arrival_greeter',
            'departure_greeter',
            'name_correcteur_greeter',
            'correction_greeter',
        )

        widgets = {
        'statut_greeter': forms.RadioSelect(),
        'genre_greeter': forms.RadioSelect(),
        'age_greeter': forms.RadioSelect(),
        'experiences_greeters': forms.CheckboxSelectMultiple(),
        'disponibility_day_greeter': forms.CheckboxSelectMultiple(),    
        'disponibility_time_greeter': forms.CheckboxSelectMultiple(),
        'list_places_greeter': forms.CheckboxSelectMultiple(),
        'interest_greeter': forms.CheckboxSelectMultiple(),
        'handicap_greeter': forms.CheckboxInput(),
        'visibily_greeter': forms.CheckboxInput(),
        'langues_parlées_greeter': forms.SelectMultiple(),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tooltips()
        self.fields['cluster'].label_from_instance = lambda obj: obj.code_cluster
        self.helper = FormHelper()
        self.helper.form_tag = True # On l'active ici car c'est le formulaire principal
        self.helper.layout = Layout(
            TabHolder(
                # ONGLET 1 : Identité & Coordonnées (User + Greeter de base)
                Tab(
                    _('Informations de base'),
                    Row(
                        Column(InlineRadios('statut_greeter'), css_class='col-md-4'),
                        Column('cluster', css_class='col-md-4'),
                        Column('destination', css_class='col-md-4'),
                    ),
                    Row(
                        Column('email', css_class='col-md-4'),
                        Column('first_name', css_class='col-md-4'),
                        Column('last_name', css_class='col-md-4'),
                    ),
                    Row(
                        Column('cellphone', css_class='col-md-4'),
                        Column('landline_phone_greeter', css_class='col-md-4'),
                        Column('whatsapp_phone_greeter', css_class='col-md-4'),
                    ),
                    Row(
                        Column(InlineRadios('genre_greeter'), css_class='col-md-4'),
                        Column(InlineRadios('age_greeter', css_class='col-md-10')),
                    ),
                    Row(
                        Column('adress1_greeter', css_class='col-md-6'),
                        Column('adress2_greeter', css_class='col-md-6'),
                    ),
                    Row(
                        Column('postalcode_greeter', css_class='col-md-4'),
                        Column('city_greeter', css_class='col-md-4'),
                        Column('country_greeter', css_class='col-md-4'),
                    ),
                    Row(
                        Column(Field('bio_greeter',rows=3), css_class='col-md-6'),
                        Column('photo', css_class='col-md-6'),
                        Column('visibily_greeter', css_class='col-md-6'),
                    ), 
                ),

                # ONGLET 2 : Profil
                Tab(
                    _('Profil'),
                    Row(
                        Column('lang_com', css_class='col-md-6'),
                        Column(Field('langues_parlées_greeter',rows=2), css_class='col-md-6'),
                    ),
                    Row(
                        Column(InlineCheckboxes('experiences_greeters'), css_class='col-md-12'),
                    ), 
                    Row(
                        Column(InlineCheckboxes('list_places_greeter'), css_class='col-md-12'),
                        
                    ),
                    Row(
                        Column(InlineCheckboxes('interest_greeter', css_class='col-md-12'))
                    ),
                
                    Row(
                        Column(InlineCheckboxes('disponibility_day_greeter'), css_class='col-md-6'),
                        Column(InlineCheckboxes('disponibility_time_greeter'), css_class='col-md-6'),
                    ),
                    Row(
                        Column('frequency_greeter', css_class='col-md-4'),
                        Column('handicap_greeter', css_class='col-md-4'),
                        Column('max_participants_greeter', css_class='col-md-4'),
                    ),
                ),
                # ONGLET 3 : Détails logistiques & Correction
                Tab(
                    _('Administration'),
                    Row(
                        Column('arrival_greeter', css_class='col-md-4'),
                        Column('departure_greeter', css_class='col-md-6'),
                    ),
                    #Row(
                    #    Column('name_correcteur_greeter', css_class='col-md-6'),
                    #    Column('correction_greeter', css_class='col-md-6'),
                   #),
                )
            ),
            Submit('submit', _('Enregistrer'), css_class='mt-3')
        )