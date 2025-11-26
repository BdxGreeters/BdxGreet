from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import (TranslationOptions, register,
                                         translator)

from cluster.models import Cluster
from core.models import (Beneficiaire, InterestCenter, Language_communication,
                         LangueDeepL, LangueParlee, No_show, Pays, Periode,
                         TrancheAge, Types_handicap)

User=get_user_model()

# Modèle Destination base 
class Destination(models.Model):
    choices = (
        ('Drafts', _("Brouillon")),
        ('Active', _("Actif")),
        ('Inactive', _("Inactif")),
        ('Désactivated', _("Désactivé"))
        )
    
    code_cluster= models.ForeignKey(Cluster,on_delete=models.PROTECT, limit_choices_to={'statut_cluster': 'Active'},related_name='cluster_destinations',verbose_name=_("Cluster"), help_text=_("Sélectionner le cluster de la destination"))
    code_dest=models.CharField(max_length=5,unique=True, default="", verbose_name=_("Code"),help_text=_("Saisir le code de la destination"))  
    code_parent_dest=models.CharField(max_length=5, default=" ",blank=True,null=True, verbose_name=_("Code parent"),help_text=_("Saisir le code parent de la destination"))    
    code_IGA_dest=models.CharField(max_length=5, default=" ",blank=True,null=True, verbose_name=_("Code IGA"),help_text=_("Saisir le code IGA de la destination"))
    name_dest=models.CharField(max_length=30,default=" ", verbose_name=_("Nom"),help_text=_("Saisir le nom de la destination"))
    desc_dest=models.TextField(max_length=100, default=" ",help_text=_("Décrire la destination"), verbose_name=_("Description"))
    adress_dest=models.CharField(max_length=250, default=" ", verbose_name=_("Adresse"),help_text=_("Saisir l'adresse de la destination"))
    region_dest=models.CharField(max_length=50, default=" ",blank=True,null= True, verbose_name=_("Région"),help_text=_("Saisir la région de la destination"))
    country_dest=models.ForeignKey(Pays, on_delete=models.PROTECT, verbose_name=_("Pays"),help_text=_("Sélectionner le pays de la destination"))
    logo_dest=models.ImageField(upload_to='logos/',default='logos/default.jpg',verbose_name=_('Logo'),blank=True, null=True,help_text=_("Taille : 250 px *250 px"))
    libelle_email_dest=models.CharField(max_length=50, default=" ", verbose_name=_("Libellé courriel émetteur "),help_text=_("Saisir le libellé des courriels émetteurs de la destination"))
    statut_dest=models.CharField(max_length=15, choices=choices, default="Drafts",help_text=_("Saisir le statut dela destination"),verbose_name=_("Statut"))
    manager_dest=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="manager_name_dest", blank=True, null=True,verbose_name=_("Nom du manager"),help_text=_("Saisir le nom du manager de la destination"))
    referent_dest=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="referent_name_dest", blank=True, null=True,verbose_name=_("Nom du référent"),help_text=_("Saisir le nom du référent de la destination"))
    matcher_dest=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="matcher_name_dest", blank=True, null=True,verbose_name=_("Nom du gestionnaire"),help_text=_("Saisir le nom du gestionnaire de la destination"))
    matcher_alt_dest=models.ForeignKey(User,on_delete=models.SET_NULL, related_name="matcher_alt_name_dest", blank=True, null=True,verbose_name=_("Nom du gestionnaire alternatif"),help_text=_("Saisir le nom du gestionnaire alternatif de la destination"))
    finance_dest=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="finance_name_dest", blank=True, null=True,verbose_name=_("Nom du gestionnaire financier"),help_text=_("Saisir le nom du gestionnaire financier de la destination"))
    list_places_dest=models.CharField(max_length=500,default=" ", verbose_name=_("Liste des lieux ou thèmes"),help_text=_("Saisir les lieux ou thèmes de la destination"))
    max_lp_dest=models.IntegerField(default=1, verbose_name=_("Nombre maximum de lieux ou thèmes"), help_text=_("Saisir le nombre maximum de lieux ou thèmes par le visiteur"))
    mini_lp_dest=models.IntegerField(default=1, verbose_name=_("Nombre minimum de lieux ou thèmes"), help_text=_("Saisir le nombre minimum de lieux ou thèmes par le visiteur"))
    max_interest_center_dest=models.IntegerField(default=1, verbose_name=_("Nombre maximum de centres d'intérêts"), help_text=_("Saisir le nombre maximum de centres d'intérêts par le visiteur"))
    mini_interest_center_dest=models.IntegerField(default=1, verbose_name=_("Nombre minimum de centres d'intérêts"), help_text=_("Saisir le nombre minimum de centres d'intérêts par le visiteur"))
    URL_retry_dest=models.URLField(default=None,blank=True,verbose_name=_('URL de retour'), help_text=_("Saisir l'URL de retour après la validation d'une demande"))
    flag_stay_dest=models.BooleanField(default=False, verbose_name=_("Dates du séjour"), help_text=_("Cocher la case si les dates du séjour sont obligatoires"))
    dispersion_param_dest=models.IntegerField(default=0, blank=True, null=True, verbose_name=_("Dispersion des dates demandées"), help_text=_("Saisir le paramètre de dispersion des dates demandées"))
    mail_notification_dest=models.EmailField(default=" ", verbose_name=_("Email de notification"),help_text=_("Saisir l'email de notification"))
    mail_response_dest=models.EmailField(default=" ", verbose_name=_("Email de réponse"),help_text=_("Saisir l'email de réponse pour un courriel envoyé par le système"))
    disability_dest=models.BooleanField(default=False,verbose_name=_("Handicap accepté"),help_text=_("Cocher la case si des visteurs ayant un handicap sont acceptés"))
    disability_libelle_dest=models.TextField(max_length=500,default=" ",blank=True,null=True,verbose_name=_("Présentation de la gestion du handicap"),help_text=_("Saisir la présentation de la gestion du handicap"))


    def save(self, *args, **kwargs):
        if self.code_dest:            
            self.code_dest=self.code_dest.upper()
        if self.code_parent_dest:
            self.code_parent_dest=self.code_parent_dest.upper()
        if self.code_IGA_dest:
            self.code_IGA_dest=self.code_IGA_dest.upper()
        super().save(*args, **kwargs)

    
    
    def __str__(self):
        return f"{self.code_dest} - {self.name_dest}  "
    
####################################################################################################
# 
# Modèle Destination Données Fonctionnelles
# 
class Destination_data(models.Model):

    choices = (
        ( 'C&G contrôlé',_('C&G contrôlé')),
        ('Greet & Greet direct',_('C&G direct')),
        ('Gest',_("Gestionnaire")),
    )


    code_dest_data =models.OneToOneField(Destination,on_delete=models.PROTECT, related_name='destination_data')
    beneficiaire_don_dest=models.ForeignKey(Beneficiaire,on_delete=models.PROTECT, related_name='beneficiaire_des_dons',verbose_name=_("Bénéficiaire des dons"), help_text=_("Sélectionner le bénéficiaire des dons pour la destination"))
    donation_proposal_dest=models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("Proposition de don"), help_text=_("Saisir la proposition de don pour la destination"))
    paypal_dest=models.URLField(default=" ",help_text=_("Saisir l'URL du compte Paypal de la destination"), verbose_name=_("Paypal de la destination"))  
    donation_text_dest=models.TextField(max_length=500,default=" ", help_text=_("Saisir le texte pour la demande de don sur le courriel du visiteur"), verbose_name=_("Texte de la demande de don"))  
    tripadvisor_dest=models.URLField(default=" ",help_text=_("Saisir l'URL de la page TripAdvisor de la destination"), verbose_name=_("TripAdvisor de la destination"))
    googlemybusiness_dest=models.URLField(default=" ",help_text=_("Saisir l'URL de la page Google My Business de la destination"), verbose_name=_("Google My Business de la destination"))
    langs_com_dest = models.ManyToManyField(Language_communication, blank=True,verbose_name=_("Langues de communication"),help_text=_("Sélectionner les langues de communication de la destination"))   
    lang_default_dest=models.ForeignKey(Language_communication,on_delete=models.PROTECT, related_name='langue_defaut_dest',verbose_name=_("Langue de communication par défaut"), help_text=_("Sélectionner la langue de communication par défaut de la destination"))
    langs_parlee_dest = models.ManyToManyField(LangueParlee, blank=True,verbose_name=_("Langues parlées"),help_text=_("Sélectionner les langues parlées dans la destination"))
    Flag_modalités_dest=models.CharField(max_length=20, choices=choices, default="C&G",help_text=_("Saisir le type de gestion de la destination"),verbose_name=_("Type de gestion"))  
    date_cg_mail_dest= models.DateField(default=None,blank=True,null=True,verbose_name=_("Date d'envoi du prochain courriel C&G"), help_text=_("Saisir la date pour l'envoi du prochain courriel de Greet & Greet"))
    periode_mail_cg_dest=models.IntegerField(default=7, verbose_name=_("Période d'envoi des courriels C&G (en jours)"), help_text=_("Saisir la période d'envoi des courriels de Greet & Greet en jours"))
    flag_cg_T_dest=models.BooleanField(default=False, verbose_name=_("Intégrer les demandes en mode  Traitement sur le mur C&G"), help_text=_("Saisir si les demandes en mode Traitement  doivent être intégrées au mur C&G"))
    flag_cg_U_dest=models.BooleanField(default=False, verbose_name=_("Intégrer les demandes en mode  Urgent sur le mur C&G"), help_text=_("Saisir si les demandes en mode Urgent  doivent être intégrées au mur C&G"))  
    flag_comment_visitor_dest=models.BooleanField(default=False, verbose_name=_("Activer les commentaires du visiteur à l'inscription"), help_text=_("Saisir si les commentaires du visteur à l'inscription sont obligatoires"))
    param_comment_visitor_dest=models.TextField(max_length=1000,default=" ",verbose_name=_("Présentation des commentaires pour le visiteur"),help_text=_("Saisir la présentation des commentaires pour le visiteur à l'inscription"))
    libelle_form_coche1_dest=models.CharField(max_length=200, default=" ", verbose_name=_("Libellé de la première case à cocher "),help_text=_("Saisir le libellé de la première case à cocher sur le formulaire d'inscription"))
    lib_url_form_coche1_dest=models.CharField(max_length=200, default=" ",help_text=_("Saisir le texte de l'URL liée à la première case à cocher sur le formulaire d'inscription"), verbose_name=_("texte de l'URL de la première case à cocher du formulaire d'inscription"))
    url_form_coche1_dest=models.URLField(default=" ",help_text=_("Saisir l'URL liée à la première case à cocher sur le formulaire d'inscription"), verbose_name=_("URL de la première case à cocher du formulaire d'inscription"))
    libelle_form_coche2_dest=models.CharField(max_length=200, default=" ", verbose_name=_("Libellé de la deuxième case à cocher "),help_text=_("Saisir le libellé de la deuxième case à cocher sur le formulaire d'inscription"))
    lib_url_form_coche2_dest=models.CharField(max_length=200, default=" ",help_text=_("Saisir le texte de l'URL liée à la deuxième case à cocher sur le formulaire d'inscription"), verbose_name=_("texte de l'URL de la deuxième case à cocher du formulaire d'inscription"))
    url_form_coche2_dest=models.URLField(default=" ",help_text=_("Saisir l'URL liée à la deuxième case à cocher sur le formulaire d'inscription"), verbose_name=_("URL de la deuxième case à cocher du formulaire d'inscription"))
    libelle_form_coche3_dest=models.CharField(max_length=200, default=" ", verbose_name=_("Libellé de la troisième case à cocher "),help_text=_("Saisir le libellé de la troisième case à cocher sur le formulaire d'inscription"))
    lib_url_form_coche3_dest=models.CharField(max_length=200, default=" ",help_text=_("Saisir le texte de l'URL liée à la troisième case à cocher sur le formulaire d'inscription"), verbose_name=_("texte de l'URL de la troisième case à cocher du formulaire d'inscription"))
    url_form_coche3_dest=models.URLField(default=" ",help_text=_("Saisir l'URL liée à la troisième case à cocher sur le formulaire d'inscription"), verbose_name=_("URL de la troisième case à cocher du formulaire d'inscription"))
    flag_request_coche1_dest=models.BooleanField(default=False, verbose_name=_("Case à cocher obligatoire 1"), help_text=_("Saisir si la première case à cocher est obligatoire sur le formulaire d'inscription"))
    flag_request_coche2_dest=models.BooleanField(default=False, verbose_name=_("Case à cocher obligatoire 2"), help_text=_("Saisir si la deuxième case à cocher est obligatoire sur le formulaire d'inscription"))
    flag_request_coche3_dest=models.BooleanField(default=False, verbose_name=_("Case à cocher obligatoire 3"), help_text=_("Saisir si la troisième case à cocher est obligatoire sur le formulaire d'inscription")) 
    flag_NoAnswer_visitor_dest=models.BooleanField(default=False, verbose_name=_("Action suite à la non-réponse du visiteur"), help_text=_("Cocher l'action à effectuer suite à la non-réponse du visiteur"))
    flag_reason_NoAnswer_greeter_dest=models.BooleanField(default=False, verbose_name=_("Demander le motif la non-réponse du Greeter"), help_text=_("SCocher si le motif de la non propsoition du Greeter est obligatoire"))
    avis_fermeture_dest=models.BooleanField(default=False, verbose_name=_("Avis de fermeture au visiteur"), help_text=_("Cocher la case pour une fermeture de la destination "))
    date_début_avis_fermeture_dest=models.DateField(default=None,blank=True,null=True,verbose_name=_("Date de début de la fermeture"), help_text=_("Saisir la date de la fermeture de la destination"))
    date_fin_avis_fermeture_dest=models.DateField(default=None,blank=True,null=True,verbose_name=_("Date de fin de la fermeture"), help_text=_("Saisir la date de fin de la fermeture de la destination"))
    texte_avis_fermeture_dest=models.TextField(max_length=1000,default=" ",verbose_name=_("Texte de l'avis de fermeture"),help_text=_("Saisir le texte de l'avis de fermeture de la destination"))
    nbre_participants_fermeture_dest=models.IntegerField(default=0, verbose_name=_("Nombre de participants en cours de fermeture"), help_text=_("Saisir le nombre de participants lors de la fermeture de la destination (0 fermeture totale)"))
    name_sign_mail_dest=models.CharField(max_length=100, default=" ", verbose_name=_("Nom pour la signature des courriels"),help_text=_("Saisir le nom pour la signature des courriels envoyés par la destination"))
    url_mail_signature_dest=models.URLField(default=" ",help_text=_("Saisir l'URL pour la signature des courriels"), verbose_name=_("URL pour la signature des courriels"))
    libelle_social1_mail_dest=models.CharField(max_length=100, default=" ", verbose_name=_("Libellé du premier réseau social"),help_text=_("Saisir le libellé du premier réseau social pour la destination"))
    url_social1_mail_dest=models.URLField(default=" ",help_text=_("Saisir l'URL du premier réseau social"), verbose_name=_("URL du premier réseau social"))
    libelle_social2_mail_dest=models.CharField(max_length=100, default=" ", verbose_name=_("Libellé du deuxième réseau social"),help_text=_("Saisir le libellé du deuxième réseau social pour la destination"))
    url_social2_mail_dest=models.URLField(default=" ",help_text=_("Saisir l'URL du deuxième réseau social"), verbose_name=_("URL du deuxième réseau social"))
    tagline_mail_dest=models.CharField(max_length=150, default=" ", verbose_name=_("Tagline pour les courriels"),help_text=_("Saisir le tagline pour les courriels envoyés par la destination"))
    titre_avis_mail_dest=models.CharField(max_length=100, default=" ", verbose_name=_("Titre de l'avis en pied des courriels"),help_text=_("Saisir le titre de l'avis en pied des courriels envoyés par la destination"))
    texte_avis_mail_dest=models.TextField(max_length=1000,default=" ",verbose_name=_("Texte de l'avis en pied des courriels"),help_text=_("Saisir le texte de l'avis en pied des courriels envoyés par la destination"))
    date_debut_avis_mail_dest=models.DateField(default=None,blank=True,null=True,verbose_name=_("Date de début de l'avis en pied des courriels"), help_text=_("Saisir la date de début de l'avis en pied des courriels"))
    date_fin_avis_mail_dest=models.DateField(default=None,blank=True,null=True,verbose_name=_("Date de fin de l'avis en pied des courriels"), help_text=_("Saisir la date de fin de l'avis en pied des courriels"))

    def __str__(self):
        return  {self.code_dest_data}
    
###################################################################################################

    # Modèle Données Flux des destinations

class Destination_flux(models.Model):

    code_dest_flux =models.OneToOneField(Destination,on_delete=models.PROTECT, related_name='destination_flux')
    frequence_mail_precoce = models.IntegerField(default=0, verbose_name=_("Fréquence des mails précoces (en jours)"), help_text=_("Saisir la fréquence des mails précoces en jours"))
    confirmation_date_precoce_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours avant le passage en mode Traitement pour l'envoi du courriel de demande de  confirmation par le visiteur"), help_text=_("Saisir le nombre de jours avant le passage en mode Traitement pour l'envoi du courriel de demande de  confirmation par le visiteur"))
    flux_treatement_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours avant le passage en mode Traitement"), help_text=_("Saisir le nombre de jours avant le passage en mode Traitement"))
    flux_urgency_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours avant le passage en mode Urgent"), help_text=_("Saisir le nombre de jours avant le passage en mode Urgent"))
    flux_delai_organisation_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours minimum avant la date de la balade"), help_text=_("Saisir le nombre de jours minimum avant la date de la balade"))
    flux_delai_max_greeter_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours maximum pour le Greeter"), help_text=_("Saisir le nombre de jours maximum pour le Greeter pour répondre à une attribution"))
    flux_frequence_relance_greeter_dest=models.IntegerField(default=0, verbose_name=_("Fréquence de relance du Greeter"), help_text=_("Saisir la fréquence pour l'envoi d'une relance au Greeter pour répondre à une attribution"))
    flux_delai_visiteur_max_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours maximum pour le visiteur"), help_text=_("Saisir le nombre de jours maximum pour le visiteur pour répondre à une proposition"))
    flux_frequence_relance_visiteur_dest=models.IntegerField(default=0, verbose_name=_("Fréquence de relance du visiteur"), help_text=_("Saisir la fréquence pour l'envoi d'une relance au visiteur pour répondre à une proposition"))
    flux_delai_pre_balade_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours avant la balade pour l'envoi du courriel de rappel au Greeter et au visiteur"), help_text=_("Saisir le nombre de jours avant la balade pour l'envoi du courriel de rappel au Greeter et au visiteur"))
    flux_saisie_suivie_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours après la balade pour la saisie manuelle d'une balade"), help_text=_("Saisir le nombre de jours après la balade pour la saisie manuelle d'une balade"))
    flux_delai_compte_rendu_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours pour l'envoi de la demande de compte-rendu au Greeter"), help_text=_("Saisir le nombre de jours après la balade pour l'envoi du courriel de demande de compte-rendu au Greeter"))
    flux_frequence_compte_rendu_dest=models.IntegerField(default=0, verbose_name=_("Fréquence de relance pour le compte-rendu du Greeter"), help_text=_("Saisir la fréquence pour l'envoi d'une relance au Greeter pour le compte-rendu"))
    flux_delai_envoi_avis_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours après la balade pour l'envoi du courriel d'avis au visiteur"), help_text=_("Saisir le nombre de jours après la balade pour l'envoi du courriel d'avis au visiteur"))
    flux_frequence_envoi_avis_dest=models.IntegerField(default=0, verbose_name=_("Fréquence de relance pour l'avis du visiteur"), help_text=_("Saisir la fréquence pour l'envoi d'une relance au visiteur pour l'avis"))
    flux_delai_avis_max_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours maximum pour le visiteur pour donner son avis"), help_text=_("Saisir le nombre de jours maximum pour le visiteur pour donner son avis"))
    flux_rgpd_dest=models.IntegerField(default=0, verbose_name=_("Nombre de jours avant l'anomysation des données"), help_text=_("Saisir le nombre de jours avant l'anomysation des données du visiteur"))

    def __str__(self):
        return  {self.code_dest_flux}  
        
###################################################################################################


