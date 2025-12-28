from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import (TranslationOptions, register,
                                         translator)

from core import data
from core.models import Language_communication, Pays



# Modele Cluster

User = get_user_model()

class Cluster(models.Model):
    choices = (
        ('Drafts', _("Brouillon")),
        ('Active', _("Actif")),
        ('Inactive', _("Inactif")),
        ('Désactivated', _("Désactivé"))       
    )

    code_cluster=models.CharField(max_length=5, default=" ",unique=True, verbose_name=_("Code"))     
    name_cluster=models.CharField(max_length=30,default=" ", verbose_name=_("Nom"))
    statut_cluster=models.CharField(max_length=15, choices=choices, default="Drafts",help_text=_("Saisir le statut du cluster"),verbose_name=_("Statut"))
    adress_cluster=models.CharField(max_length=100,default=" ", verbose_name=_("Adresse"))
    desc_cluster=models.TextField(max_length=500,default=" ", help_text=_("Décrire les zones géographiques du cluster"), verbose_name=_("Description"))
    paypal_cluster= models.URLField(default=" ",help_text=_("URL du compte Paypal du cluster"), verbose_name=_("Paypal du cluster"))
    admin_cluster=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="admin_cluster", null=True, blank=True, verbose_name=_("Nom"),help_text=_("Saisir l'administrateur parmi les utilisateurs ou en créer un"))
    country_admin_cluster=models.ForeignKey(Pays,on_delete=models.SET_NULL,related_name=  "country_admin_cluster",null=True, blank=True,default=" ", verbose_name=_("Pays"),help_text=_("Saisir le pays de l'administrateur"))
    admin_alt_cluster = models.ForeignKey(User,on_delete=models.SET_NULL,related_name="admin_alt_cluster", null=True, blank=True, verbose_name=_("Nom"),help_text=_("Saisir l'administrateur alternatif parmi les utilisateurs ou en créer un"))
    country_admin_alt_cluster= models.ForeignKey(Pays,on_delete=models.SET_NULL,related_name="country_admin_alt_cluster",null=True, default=" ",blank=True, verbose_name=_("Pays"), help_text=_("Saisir le pays de l'admnistrateur alternatif"))
    param_nbr_part_cluster= models.IntegerField(default= data.MAX_VISITOR,  help_text=_("Nombre maximun de visiteurs pour le cluster"), verbose_name=_("Nombre maximun de participants"))
    langs_com = models.ManyToManyField(Language_communication, related_name="langs_com",verbose_name=_("Langues de communication"),help_text=_("Sélectionner les langues de communication du cluster"))
    backup_mails_cluster=models.EmailField(default=" ",help_text=_("Adresse de sauvegarde des courriels générés sur l'ensemnble du cluster"), verbose_name=_("Adresse  de sauvegarde des courriels"))
    url_biblio_cluster=models.URLField(default=" ",blank=True, help_text=(_("Saisir l'URL de la bibliothèque pour les destinations")) ,verbose_name=_("URL de la bibliothèque Cluster des destinations"))
    url_biblio_Greeter_cluster=models.URLField(default=" ",blank=True,help_text=(_("Saisir l'URL de la bibliothèque pour les Greeter")), verbose_name=_("URL de la bibliothèque Cluster des Greeter"))
    list_experience_cluster=models.ManyToManyField('Experience_Greeter', related_name="list_experience_cluster")
    profil_interet_cluster=models.ManyToManyField('InterestCenter', related_name="profil_interet_cluster")
    reason_no_reply_greeter_cluster=models.ManyToManyField('Reason_No_Response_Greeter', related_name="reason_no_reply_greeter_cluster")
    reason_no_reply_visitor_cluster=models.ManyToManyField('Reason_No_Response_Visitor', related_name="reason_no_reply_visitor_cluster")
    list_notoriety_cluster=models.ManyToManyField('Notoriety', related_name="list_notoriety_cluster")
    
    def clean(self):
        super().clean()
        
        # Nombre maximum de participants
        
        max_value =data.MAX_VISITOR
        if self.param_nbr_part_cluster > max_value:
            raise ValidationError(_("Le nombre maximum de participants est de {}.").format(max_value))
    
    def save (self, *args, **kwargs):
        self.code_cluster=self.code_cluster.upper()
        super().save(*args, **kwargs)
      
    def __str__(self):
        return self.code_cluster
###################################################################################################

# Modèle  Liste des expériences Greeters

class Experience_Greeter(models.Model):
    experience_greeter=models.CharField(max_length=100, default="Pas d'expérience", verbose_name=_("Expérience"), help_text=_("Saisir l'expérience du Greeter"))
    
    def __str__(self):
        return self.experience_greeter
    
###################################################################################################

# Modèle Centres d'intérêt

class InterestCenter(models.Model):

    interest_center=models.CharField(max_length=100, verbose_name=_("Centre d'intérêt"))

    def __str__(self):
        return f"{self.interest_center}"
        
###################################################################################################

# Modèle Raison des non réponses du Greeter

class Reason_No_Response_Greeter (models.Model):
    reason_no_reply_greeter=models.CharField(max_length=100, verbose_name=_("Raison de non réponse du Greeter"))

    def __str__(self):
        return f"[{self.reason_no_response_greeter}]"

###################################################################################################

# Modèle Raison non réponse du visiteur

class Reason_No_Response_Visitor (models.Model):
    reason_no_reply_visitor=models.CharField(max_length=100, verbose_name=_("Raison de non réponse du visiteur"))

    def __str__(self):
        return f"[{self.reason_no_response_visitor}]"

###################################################################################################

# Modèle Notoriété des expériences Greeter

class Notoriety(models.Model):
    notoriety=models.CharField(max_length=100, verbose_name=_("Notoriété"))

    def __str__(self):
        return f"[{self.notoriety}]"
    
###################################################################################################