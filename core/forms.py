from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from core.models import (Beneficiaire, Email_Mailjet, InterestCenter,
                         LangueDeepL, No_show, Periode, TrancheAge,
                         Types_handicap)


# Form Création d'un email_Mailjet
class   Email_MailjetCreationForm (forms.ModelForm):
    class Meta:
        model=Email_Mailjet
        fields=('code_email','name_email','lang_email','id_mailjet_email')
###################################################################################################

# Form Création d'une langue prise en charge par Deepl
class LangueDeepLCreationForm (forms.ModelForm):
    class Meta:
        model=LangueDeepL    
        fields=('code_iso','lang_deepl')
###################################################################################################

# Form Création d'un centre d'intérêt

class InterestCenterCreationForm (forms.ModelForm):
    class Meta:
        model= InterestCenter
        fields =('interest_center',)
###################################################################################################

# Form Création d'une raison de non réalisation de l'expérience

class No_showCreationForm (forms.ModelForm):
    class Meta:
        model= No_show
        fields=('raison_noshow',)
###################################################################################################

# Form Création d'un bénéficiare d'un don

class BeneficiaireCreationForm (forms.ModelForm):
    class Meta:
        model= Beneficiaire
        fields=("nom_beneficiaire",)
###################################################################################################

# Form Création d'une période de la journée

class PeriodeCreationForm (forms.ModelForm):
    class Meta:
        model= Periode
        fields=("periode_journee",)
###################################################################################################

# Form Création d'une tranche d'âge

class TrancheAgeCreationForm (forms.ModelForm):
    class Meta:
        model= TrancheAge
        fields =('tranche_age',)
###################################################################################################

# Form Création d'un type de handicap

class Types_handicapCreationForm (forms.ModelForm):
    class Meta:
        model= Types_handicap
        fields=('type_handicap',)
###################################################################################################        