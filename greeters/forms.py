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
from destination.models import Destination,Destination_data,List_places
from core.models import Language_communication
from django.utils import timezone

User=get_user_model()

class GreeterCombinedForm(HelpTextTooltipMixin, forms.ModelForm):
    # On définit ici les champs de CustomUser que l'on veut ajouter au formulaire Greeter
    email = forms.EmailField(label=_("Email"),help_text=_("Saisir l'adresse courriel du Greeter"))
    first_name = forms.CharField(label=_("Prénom"), help_text=_("Saisir le prénom du Greeter"))
    last_name = forms.CharField(label=_("Nom"), help_text=_("Saisir le nom du Greeter"))
    cellphone = forms.CharField(label=_("Téléphone Mobile"), help_text=_("Saisir le numéro de téléphone mobile du Greeter"))
    lang_com = lang_com = forms.ModelChoiceField(
        label=_("Langue de communication"),
        queryset=Language_communication.objects.none(),  # On va définir le queryset dans __init__ pour filtrer selon le groupe de l'admin
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
            'indisponibilty',
            'begin_indisponibility',
            'end_indisponibility',
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
        'indisponibilty': forms.CheckboxInput(),
        'begin_indisponibility': forms.DateInput(attrs={'type': 'date'}),
        'end_indisponibility': forms.DateInput(attrs={'type': 'date'}),
        'list_places_greeter': forms.CheckboxSelectMultiple(),
        'interest_greeter': forms.CheckboxSelectMultiple(),
        'handicap_greeter': forms.CheckboxInput(),
        'visibily_greeter': forms.CheckboxInput(),
        'langues_parlées_greeter': forms.SelectMultiple(),
        'arrival_greeter': forms.DateInput(attrs={'type': 'date'}),
        'departure_greeter': forms.DateInput(attrs={'type': 'date'}),
        }
    
    
    def clean_begin_date(self):
        
        begin_date = self.cleaned_data.get('begin_indisponibility')
        today = timezone.now().date()
    
        if begin_date and begin_date < today:
            raise forms.ValidationError(_("La date de début ne peut pas être dans le passé."))
        
        arrival_date = self.cleaned_data.get('arrival_greeter')
        if arrival_date and begin_date and begin_date > arrival_date:
            raise forms.ValidationError(_("La date de début ne peut pas être après la date d'arrivée."))
        
        return begin_date

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
    
    # On cherche si un utilisateur utilise déjà cet email
        users_with_same_email = User.objects.filter(email=email)
    
    # Si c'est une modification (instance existe déjà)
        if self.instance and self.instance.pk:
            # On exclut l'utilisateur lié à ce Greeter de la recherche
            users_with_same_email = users_with_same_email.exclude(pk=self.instance.user.pk)
    
        if users_with_same_email.exists():
            raise forms.ValidationError(_("Cette adresse email est déjà utilisée par un autre utilisateur."))
    
        return email

    def __init__(self, *args, **kwargs):
        self.admin = kwargs.pop('admin_greeter', None)
        super().__init__(*args, **kwargs)
        
        destination_obj= None
        cluster_obj= None

        #si le code_cluster est connu
        if self.admin and self.admin.code_cluster:
            cluster_obj= Cluster.objects.get(code_cluster=self.admin.code_cluster)
            self.fields['interest_greeter'].queryset = cluster_obj.interest_center.all()
            self.fields['experiences_greeters'].queryset = cluster_obj.experience_greeter.all()
            self.fields['cluster'].disabled = True
        
        #si le code_dest est connu
        if self.admin and self.admin.code_dest:
            self.fields['destination'].disabled = True
            self.fields['country_greeter'].disabled = True
            destination_obj= Destination.objects.get(code_dest=self.admin.code_dest)
            dest_data= Destination_data.objects.get(code_dest_data=self.admin.code_dest)
            lang_ids = list(dest_data.langs_com_dest.values_list('id', flat=True))
            if dest_data.lang_default_dest:
                lang_ids.append(dest_data.lang_default_dest.id)
            self.fields['lang_com'].queryset = Language_communication.objects.filter(id__in=lang_ids).distinct()
            self.fields['lang_com'].initial = dest_data.lang_default_dest
            self.fields['destination'].queryset = Destination.objects.filter(code_cluster=destination_obj.code_cluster)
            self.fields['list_places_greeter'].queryset = destination_obj.list_places_dest.all()

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
                        Column('indisponibilty', css_class='col-md-3'),
                        Column('begin_indisponibility', css_class='col-md-3'),
                        Column('end_indisponibility', css_class='col-md-3'),
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