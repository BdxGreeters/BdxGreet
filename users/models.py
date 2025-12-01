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
    email = models.EmailField(unique=True, verbose_name=_('Courriel'))
    first_name = models.CharField(max_length=150, verbose_name=_("Prénom"))
    last_name = models.CharField(max_length=150, verbose_name=_("Nom"))
    cellphone =models.CharField(max_length=15,blank=True, null=True,verbose_name=_('Téléphone portable'))
    lang_com= models.CharField(max_length=10, choices=settings.LANGUAGES, default='fr', verbose_name=_("Langue de communication"))
    code_cluster=models.CharField(max_length=5, default="",blank=True, null=True,verbose_name=_('Code du cluster'))
    code_dest=models.CharField(max_length=5, default="",blank=True, null=True,verbose_name=_('Code de la destination'))
    
    
    objects = CustomUserManager()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name','cellphone','lang_com']

    def save(self, *args, **kwargs):
        if self.code_cluster:
            self.code_cluster = self.code_cluster.upper()
        
        if self.code_dest:
            self.code_dest = self.code_dest.upper()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Greeter(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.PROTECT)
    adress1 = models.CharField(max_length=100,verbose_name=_('Adresse'))
    adress2 = models.CharField(max_length=100,blank=True, null=True, verbose_name=_("Complément d'adresse"))
    postal_code = models.CharField(max_length=5,verbose_name=_('Code postal'))
    city = models.CharField(max_length=40, verbose_name=_('Ville'))
    landline =models.CharField(max_length=15,blank=True, null=True,verbose_name=_('Téléphone fixe)'))
    date_birth = models.DateField(auto_now=False, blank=True, null=True,verbose_name=_('Date de naissance'))
    job= models.CharField(max_length=20,blank=True, null=True,verbose_name=_('Profession'))
    photo = models.ImageField (upload_to ='photos_profil/',default='photos_profil/default.jpg', verbose_name=_('Photo de profil'), help_text=_("Taille : 200 px *200 px"))



    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
