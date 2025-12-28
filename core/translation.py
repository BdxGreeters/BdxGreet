from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import (TranslationOptions, register,
                                         translator)

from cluster.models import Cluster, Experience_Greeter, InterestCenter, Notoriety, Reason_No_Response_Greeter, Reason_No_Response_Visitor
from core.models import (Beneficiaire, InterestCenter, Language_communication,
                         LangueDeepL, LangueParlee, No_show, Pays, Periode,
                         TrancheAge, Types_handicap)
from destination.models import Destination, Destination_data

###################################################################################################

# Traduction des modèles du core

class LangueDeepLTranslationOptions(TranslationOptions):
    fields = ('lang_deepl',)

translator.register(LangueDeepL, LangueDeepLTranslationOptions) 


class LangueParleeTranslationOptions(TranslationOptions):
    fields =('langue_parlee',)

translator.register(LangueParlee, LangueParleeTranslationOptions)

class PaysTranslationOptions(TranslationOptions):
    fields =('nom_pays',)

translator.register(Pays, PaysTranslationOptions)   

class No_showTranslationOptions(TranslationOptions):
    fields =('raison_noshow',)

translator.register(No_show, No_showTranslationOptions)   

class PeriodeTranslationOptions(TranslationOptions):
    fields =('periode_journee',)

translator.register(Periode, PeriodeTranslationOptions)

class TrancheAgeTranslationOptions(TranslationOptions):
    fields =('tranche_age',)

translator.register(TrancheAge, TrancheAgeTranslationOptions)

class Types_handicapTranslationOptions(TranslationOptions):
    fields =('type_handicap',)

translator.register(Types_handicap, Types_handicapTranslationOptions)

class Language_communicationTranslationOptions(TranslationOptions):
    fields =('name',)

translator.register(Language_communication, Language_communicationTranslationOptions)

###################################################################################################

# Traduction des modèles Cluster

class Experience_GreeterTranslationOptions(TranslationOptions):
    fields =('experience_greeter',)

translator.register(Experience_Greeter, Experience_GreeterTranslationOptions)

class InterestCenterTranslationOptions(TranslationOptions):
    fields =('interest_center',)

translator.register(InterestCenter, InterestCenterTranslationOptions)


###################################################################################################

# Traduction des modèles Destination

class DestinationTranslationOptions(TranslationOptions):
    fields =('list_places_dest','disability_libelle_dest',)

translator.register(Destination, DestinationTranslationOptions) 

class BeneficiaireTranslationOptions(TranslationOptions):
    fields =('nom_beneficiaire',)

translator.register(Beneficiaire, BeneficiaireTranslationOptions)

class Destination_dataTranslationOptions(TranslationOptions):
    fields=('donation_text_dest','param_comment_visitor_dest','libelle_form_coche1_dest', 'lib_url_form_coche1_dest', 'libelle_form_coche2_dest', 'lib_url_form_coche2_dest', 'libelle_form_coche3_dest', 'lib_url_form_coche3_dest','texte_avis_fermeture_dest','tagline_mail_dest','texte_avis_mail_dest')

translator.register(Destination_data, Destination_dataTranslationOptions)