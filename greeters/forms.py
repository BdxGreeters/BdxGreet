from django import forms
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

User=get_user_model()

class CustomUserCreationForm(HelpTextTooltipMixin,forms.ModelForm):
    class Meta:
        model = CustomUser  
        fields = (
            'email',
            'first_name',
            'last_name',
            'cellphone',
            'lang_com'
                  )
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'lang_com': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # IMPORTANT: Empêche Crispy de générer une balise <form>
        self.helper.layout = Layout(
            Row(
                Column('email', css_class='col-md-4'),
                Column('first_name', css_class='col-md-4'),
                Column('last_name', css_class='col-md-4'),
            ),
            Row(
                Column('cellphone', css_class='col-md-4'),
                Column('lang_com', css_class='col-md-4'),
            ),
                
        )


class GreeterCreationForm(HelpTextTooltipMixin,forms.ModelForm):
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
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag= False
        self.helper.layout = Layout(
            Row(
                Column('statut_greeter', css_class='col-md-4'),
            ),
            Row(
                Column('genre_greeter', css_class='col-md-4'),
            ),
            Row(
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
                Column('landline_phone_greeter', css_class='col-md-4'),
                Column('whatsapp_phone_greeter', css_class='col-md-4'),
            ),
            Row(
                Column('experiences_greeters', css_class='col-md-6'),
            ),
            Row(
                Column('photo', css_class='col-md-6'),
                Column('bio_greeter', css_class='col-md-6'),
            ),
            Row(
                Column('handicap_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('visibily_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('langues_parlées_greeter', css_class='col-md-4'),
            ),
            Row(
                Column('max_participants_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('disponibility_day_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('disponibility_time_greeter', css_class='col-md-12'),
            ),
    
            Row(
                Column('frequency_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('comments_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('interest_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('list_places_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('arrival_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('departure_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('name_correcteur_greeter', css_class='col-md-12'),
            ),
            Row(
                Column('correction_greeter', css_class='col-md-12'),
            ),
        )

