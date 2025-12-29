from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import (TranslationOptions, register,
                                         translator)

###################################################################################################
# Modele de la liste des courriels Mailjet

class Email_Mailjet(models.Model):
    code_email=models.CharField(max_length=5, unique=True, verbose_name=_('Code_courriel'))
    name_email=models.CharField(max_length=100, verbose_name=_('Nom_courriel'))
    lang_email=models.CharField(max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE, verbose_name=_('Langue'))
    id_mailjet_email =models.IntegerField(verbose_name="Id_template_mailjet")

    def __str__(self):
        return f"{self.code_email} -{self.name_email} -{self.id_mailjet_email}"
    
###################################################################################################

# Modèle contenant les langues supportées par Deepl

class LangueDeepL(models.Model):
    code_iso = models.CharField(max_length=10, unique=True)
    lang_deepl=models.CharField(max_length=100,default="Français", verbose_name=_("Langue"))

    def __str__(self):
        return f"{self.lang_deepl} ({self.code_iso})"
###################################################################################################

# Modèle Langues parlées

class LangueParlee(models.Model):
    code_iso = models.CharField(max_length=2, unique=True) 
    langue_parlee=models.CharField(max_length=100, verbose_name=_("Langue parlée"))

    def __str__(self):
        return f"{self.langue_parlee}"
###################################################################################################

# Modèle Liste des pays

class Pays(models.Model):
    code_iso=models.CharField(max_length=3, unique=True)
    nom_pays=models.CharField(max_length=100, verbose_name=_("Pays"))

    class Meta:
        ordering = ['nom_pays']  # Tri par ordre alphabétique du champ 'nom'
        verbose_name_plural = "Pays"


    def __str__(self):
        return f"{self.nom_pays}"
###################################################################################################

# Modèle Liste des raisons non réalisation

class No_show(models.Model):
    raison_noshow=models.CharField(max_length=100,default="Pas de raison", verbose_name=_("Raison non réalisation"))

    def __str__(self):
        return f"{self.raison_noshow}"
###################################################################################################

#Modèle Liste des bénéficiaires des dons

class Beneficiaire(models.Model):
    nom_beneficiaire=models.CharField(max_length=100,default="Pas de donation",verbose_name=_("Nom du bénéficiaire"))

    def __str__(self):
        return f"{self.nom_beneficiaire}"
###################################################################################################    

# Modèle Période de la journée

class Periode(models.Model):
    periode_journee=models.CharField(max_length=100,default='Dans la journée', verbose_name=_("Période de la journée"))

    def __str__(self):
        return f"{self.periode_journee}"
###################################################################################################

# Modèle Tranches d'âges
 
class TrancheAge(models.Model):
    tranche_age=models.CharField(max_length=100, default="Adulte (30-65)", verbose_name=_("Tranche d'âge"))

    def __str__(self):
        return f"{self.tranche_age}"
###################################################################################################

# Modèle Types_handicap

class Types_handicap(models.Model):
    type_handicap=models.CharField(max_length=50, default="Pas de handicap", verbose_name=_("Type de handicap"))

    def __str__(self):
        return f"{self.type_handicap}"
###################################################################################################

# Modèle Langue de communication

class Language_communication(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

####################################################################################################
 # Modèle FieldsPermission_


class FieldPermission(models.Model):
    field_name = models.CharField(max_length=100)
    is_editable = models.BooleanField(default=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    group = models.ManyToManyField(Group, related_name="fields_permissions")
    target_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="target_permissions")
    app_name = models.CharField(max_length=50)  # Ex: "cluster" ou "destination"

    class Meta:
        unique_together = ('field_name', 'content_type', 'object_id', 'target_group', 'app_name')
        verbose_name = "Permission de champ"
        verbose_name_plural = "Permissions de champs"

    def __str__(self):
        return self.field_name 
###################################################################################################


