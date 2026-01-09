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


User=get_user_model()

class GreeterCombinedForm(HelpTextTooltipMixin, forms.ModelForm):
    # On définit ici les champs de CustomUser que l'on veut ajouter au formulaire Greeter
    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(label=_("Prénom"))
    last_name = forms.CharField(label=_("Nom"))
    cellphone = forms.CharField(label=_("Mobile"))
    lang_com = lang_com = forms.ChoiceField(
        label=_("Langue de communication"),
        choices=settings.LANGUAGES, 
        initial=settings.LANGUAGE_CODE, # Optionnel : définit la langue par défaut du site
        widget=forms.Select(attrs={'class': 'form-control'}) )# Adaptez selon vos choix

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
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tooltips()
        self.helper = FormHelper()
        self.helper.form_tag = True # On l'active ici car c'est le formulaire principal
        self.helper.layout = Layout(
            TabHolder(
                # ONGLET 1 : Identité & Coordonnées (User + Greeter de base)
                Tab(
                    _('Informations de base'),
                    Row(
                        Column(InlineRadios('statut_greeter'), css_class='col-md-4'),
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
                        Column('lang_com', css_class='col-md-6'),
                    ),
                    Row(
                        Column(InlineRadios('genre_greeter'), css_class='col-md-4'),
                        Column('age_greeter', css_class='col-md-4'),
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
                        
                    ),
                ),

                # ONGLET 2 : Profil & Disponibilités
                Tab(
                    _('Profil et Disponibilités'),
                    Row(
                        Column(InlineCheckboxes('experiences_greeters'), css_class='col-md-8'),
                        Column('photo', css_class='col-md-4'),
                    ),
                    Row(Column(Field('bio_greeter',rows=3), css_class='col-md-12')),
                    Row(Column('langues_parlées_greeter', css_class='col-md-6')),
                    Row(
                        Column(InlineCheckboxes('disponibility_day_greeter'), css_class='col-md-6'),
                        Column('disponibility_time_greeter', css_class='col-md-6'),
                    ),
                    Row(Column('frequency_greeter', css_class='col-md-4')),
                ),

                # ONGLET 3 : Détails logistiques & Correction
                Tab(
                    _('Logistique et Administration'),
                    Row(Column('list_places_greeter', css_class='col-md-12')),
                    Row(
                        Column('arrival_greeter', css_class='col-md-6'),
                        Column('departure_greeter', css_class='col-md-6'),
                    ),
                    Row(
                        Column('interest_greeter', css_class='col-md-6'),
                        Column('max_participants_greeter', css_class='col-md-6'),
                    ),
                    Row(
                        Column('name_correcteur_greeter', css_class='col-md-6'),
                        Column('correction_greeter', css_class='col-md-6'),
                    ),
                )
            ),
            Submit('submit', _('Enregistrer'), css_class='mt-3')
        )