from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        Group, PermissionsMixin)
from django.db import models
from users.models import CustomUser
from core.models import TrancheAge,LangueParlee, Pays, Periode
from cluster.models import Experience_Greeter
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Modèle du Greeter

class Greeter(models.Model):
    
    choices_statut= (
        ('Drafts', _("Brouillon")),
        ('Active', _("Actif")),
        ('Inactive', _("Inactif")),
        ('Archived', _("Archivé"))
        )
    
    choices_genre= (
        ('M', _("Masculin")),
        ('F', _("Féminin")),
        ('X', _("Autre"))
        )

    choices_day=(
        ('Lundi', _("Lundi")),
        ('Mardi', _("Mardi")),
        ('Mercredi', _("Mercredi")),
        ('Jeudi', _("Jeudi")),
        ('Vendredi', _("Vendredi")),
        ('Samedi', _("Samedi")),
        ('Dimanche', _("Dimanche"))
    )

    user = models.OneToOneField(CustomUser, on_delete=models.PROTECT)
    statut_greeter=models.CharField(max_length=15,choices=choices_statut,default="Drafts",verbose_name=_('Statut'),help_text=_("Saisir le statut du Greeter"))
    genre_greeter=models.CharField(max_length=1,choices=choices_genre, default="X",verbose_name=_('Genre'),help_text=_("Saisir le genre du Greeter"))
    adress1_greeter=models.CharField(max_length=50,default="",verbose_name=_('Adresse 1'),help_text=_("Saisir l'adresse du Greeter"))
    adress2_greeter=models.CharField(max_length=50,default="",blank=True,null=True,verbose_name=_('Adresse 2'),help_text=_("Saisir l'adresse complémentaire du Greeter"))
    postalcode_greeter=models.CharField(max_length=5,default="",verbose_name=_('Code postal'),help_text=_("Saisir le code postal du Greeter"))
    city_greeter=models.CharField(max_length=50,default="",verbose_name=_('Ville'),help_text=_("Saisir la ville du Greeter"))
    country_greeter=models.ForeignKey(Pays, on_delete=models.PROTECT,max_length=50,default="",verbose_name=_('Pays'),help_text=_("Saisir le pays du Greeter"))
    landline_phone_greeter=models.CharField(max_length=20,default="",blank=True,null=True,verbose_name=_('Téléphone fixe'),help_text=_("Saisir le numéro de téléphone fixe du Greeter"))
    whatsapp_phone_greeter=models.CharField(max_length=20,default="",blank=True,null=True,verbose_name=_('Téléphone whatsapp'),help_text=_("Saisir le numéro de téléphone whatsapp du Greeter"))
    age_greeter=models.ForeignKey(TrancheAge, on_delete=models.PROTECT,verbose_name=_("Tranche d'âge"),help_text=_("Saisir la tranche d'âge du Greeter"))
    experiences_greeters=models.ManyToManyField(Experience_Greeter, blank=True,verbose_name=_('Expériences de Greeter'),help_text=_("Saisir les expériences de Greeter"))
    photo = models.ImageField (upload_to ='photos_profil/',default='photos_profil/default.jpg', verbose_name=_('Photo de profil'), help_text=_("Taille : 200 px *200 px"))
    bio_greeter=models.TextField(max_length=1500,default="",verbose_name=_('Biographie'),help_text=_("Saisir la biographie du Greeter"))
    handicap_greeter=models.BooleanField(default=False,verbose_name=_('Accepte des balades avec des personnes ayant un handicap'),help_text=_("Saisir si le Greeter accepte des balades avec des personnes ayant un handicap"))
    visibily_greeter=models.BooleanField(default=False,verbose_name=_('Accepte que sa photo soit transmise au visiteur'),help_text=_("Saisir si le Greeter accepte que sa photo soit transmise au visiteur"))
    langues_parlées_greeter=models.ManyToManyField(LangueParlee, blank=True,max_length=100,default="",verbose_name=_('Langues parlées'),help_text=_("Saisir les langues parlées du Greeter"))
    max_participants_greeter=models.IntegerField(default=6,verbose_name=_('Nombre maximum de participants'),help_text=_("Saisir le nombre maximum de participants accepté par le Greeter"))
    disponibility_day_greeter=models.CharField(choices=choices_day,max_length=100,default="Lundi, Mardi, Mercredi, Jeudi, Vendredi, Samedi, Dimanche",verbose_name=_('Jours de disponibilité'),help_text=_("Saisir les jours de disponibilité du Greeter")) # Lundi, Mardi, Mercredi, Jeudi, Vendredi, Samedi, Dimanche
    disponibility_time_greeter=models.ManyToManyField(Periode,max_length=100,default="",blank=True,null=True,verbose_name=_('Disponibilité en journée'),help_text=_("Saisir les périodes de disponibilité en journée du Greeter"))
    frequency_greeter=models.IntegerField(default=1, verbose_name=_('Intervalle en jours entre deux balades'),help_text=_("Saisir l'intervalle en jours entre deux balades"))
    comments_greeter=models.TextField(max_length=1500,default="",blank=True,null=True,verbose_name=_('Commentaires'),help_text=_("Saisir les commentaires du Greeter"))
    interest_greeter=models.CharField(max_length=300,default="",verbose_name=_('Intérêts'),help_text=_("Saisir les centres d'intérêts du Greeter"))
    list_places_greeter=models.CharField(max_length=300,default="",verbose_name=('Thèmes ou lieux'),help_text=_("Saisir les cethèmes ou lieux du Greeter"))
    arrival_greeter=models.DateField(verbose_name=_("Date d'arrivée"),help_text=_("Saisir la date d'arrivée du Greeter"))
    departure_greeter=models.DateField(verbose_name=_('Date de départ'),blank=True,null=True,help_text=_("Saisir la date de départ du Greeter"))
    modif_greeter=models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=_('Date de dernière modification'),help_text=_("Saisir la date de dernière modification du Greeter"))
    name_correcteur_greeter=models.CharField(max_length=30,default="",blank=True,null=True,verbose_name=_('Nom du correcteur'),help_text=_("Saisir le nom du correcteur"))
    correction_greeter=models.TextField(max_length=1000,default="",blank=True,null=True,verbose_name=_('Corrections de la fiche Greeter'), help_text=_("Saisir les corrections de la fiche Greeter"))
                                    
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
###################################################################################################

# Modèle des indisponibilités
     
class Indisponibility(models.Model):
    greeter_indisponibility = models.OneToOneField(Greeter, on_delete=models.CASCADE, related_name='indisponibilities')
    start_date_indisponibility = models.DateField(blank=True, null=True,verbose_name=_("Date de début"), help_text=_("Saisir la date de début de l'indisponibilité"))
    end_date_indisponibility = models.DateField(blank=True, null=True, verbose_name=_('Date de fin'), help_text=_("Saisir la date de fin de l'indisponibilité"))
    comments_indisponibility = models.CharField(max_length=255, blank=True, null=True,verbose_name=_('Commentaires'),help_text=_("Saisir les commentaires de l'indisponibilité"))

    class Meta:
        verbose_name = _("Indisponibilité")
        verbose_name_plural = _("Indisponibilités")

    def __str__(self):
        return f"{self.greeter.user.first_name} {self.greeter.user.last_name} -indisponible du {self.start_date} au {self.end_date}"

###################################################################################################

# Modèle du greet-type

class GreeterType(models.Model):
    greeter_greet_type=models.ForeignKey(Greeter, on_delete=models.CASCADE, related_name='greet_types')
    langue_greet_type=models.CharField(max_length=20 ,default="",verbose_name=_('Langue du greet-type'),help_text=_("Saisir la langue parlée du greet-type"))
    titre_greet_type=models.CharField(max_length=50,default="",verbose_name=_('Titre du greet-type'),help_text=_("Saisir le titre du greet-type dans la langue du greet-type"))
    list_places_greet_type=models.CharField(max_length=300,default="",verbose_name=_('Thèmes ou lieux'),help_text=_("Saisir les cethèmes ou lieux du greet-type"))  
    rv_greet_type=models.CharField(max_length=100, default="", verbose_name=_('Lieu du rendezz-vous'),help_text=_("Saisir le lieu du rendezz-vous"))
    maps_greet_type=models.URLField(max_length=200,default="",blank=True,null=True, verbose_name=_('Lien Google Maps'),help_text=_("Saisir le lien Google Maps du lieu de rendez-vous"))
    description_greet_type=models.TextField(max_length=500,default="",verbose_name=_('Description'),help_text=_("Saisir la description du greet-type"))
    photo_greet_type=models.ImageField(upload_to ='photos_profil/',default='photos_profil/default.jpg', verbose_name=_('Photo du greet-type'), help_text=_("Taille : 1200 px * 900 px"))

    def __str__(self):
        return f"{self.greeter.user.first_name} {self.greeter.user.last_name} -greet-type {self.description_greet_type}"

###################################################################################################