from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        Group, PermissionsMixin)
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Gestionnaire pour le modèle utilisateur personnalisé."""

    def create_user(self, email, first_name, last_name,password=None, **extra_fields):
        
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name , last_name=last_name, **extra_fields)
        # On ne définit pas de mot de passe utilisable initialement
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password,first_name,last_name, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        # Pour le superuser, on crée un utilisateur standard d'abord (sans mot de passe)
        # puis on définit le mot de passe.
        user = self.model(email=self.normalize_email(email), first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Modèle utilisateur personnalisé utilisant l'email comme identifiant."""
    email = models.EmailField(unique=True, verbose_name=_('Courriel'), help_text=_("Saisir l'adresse email"))
    first_name = models.CharField(max_length=150, verbose_name=_("Prénom"),help_text=_("Saisir le prénom"))
    last_name = models.CharField(max_length=150, verbose_name=_("Nom"), help_text=_("Saisir le nom de famille"))
    cellphone =models.CharField(max_length=15,blank=True, null=True,verbose_name=_('Téléphone portable'), help_text=_("Saisir le numéro de téléphone portable"))
    lang_com= models.CharField(max_length=10, choices=settings.LANGUAGES, default='fr', verbose_name=_("Langue de communication"), help_text=_("Saisir la langue de communication"))
    code_cluster=models.ForeignKey('cluster.Cluster',on_delete=models.SET_NULL, blank=True, null=True,verbose_name=_('Code du cluster'), help_text=_("Saisir le code du cluster"))
    code_dest=models.ForeignKey('destination.Destination', on_delete=models.SET_NULL,blank=True, null=True,verbose_name=_('Code de la destination'), help_text=_("Saisir le code de la destination"))

    
    
    objects = CustomUserManager()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name','cellphone','lang_com']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


