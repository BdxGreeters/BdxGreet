import deepl
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from core.models import Email_Mailjet, InterestCenter
from users.models import Greeter
from users.tasks import reset_password, send_email_mailjet

###################################################################################################
#Signal permettant d'envoyer le courrier de création du mot de passe
User = get_user_model() 
@receiver(post_save, sender=User)
def afficher_domaine_actuel(sender, instance, created, **kwargs):
    if created:
        request = kwargs.get('request')
        if request:
            current_site = get_current_site(request)
            code_email="SETPW"
            id_template_mailjet= Email_Mailjet.objects.get(code_email=code_email, lang_email=instance.user.lang_com).id_mailjet_email
            reset_password (instance.id,current_site, id_template_mailjet)
            print(f"_(Nouvel utilisateur créé sur le domaine : {current_site.domain})")
        else:
            print(_("Aucun objet request trouvé pour obtenir le domaine actuel."))
###################################################################################################

# Signal permettant de connaitre les champs modifiés lors d'une mise à jour d'un Greeter

@receiver(pre_save,sender=Greeter)
def capture_etat_initial(sender,instance,**kwargs):
    if instance.pk:
        try:
            instance._original_state=Greeter.objects.get(pk=instance.pk)
        except Greeter.DoesNotExist:
            instance._original_state =None
@receiver(post_save, sender=Greeter)
def notifier_modified_fields( sender, instance,created,**kwargs):
    if created or not hasattr(instance, '_original_state') or instance._original_state is None:
        return
    
    modified_fields=[]
    original_state = instance._original_state
    
    for field in instance._meta.fields:
        field_name =field.name
        old_value = getattr(original_state, field_name)
        new_value = getattr(instance, field_name)
        field_name = field.verbose_name  # Utilisation du verbose_name au lieu du nom du champ

        if old_value != new_value:
            modified_fields.append ({'field_name':field_name,'old_value':old_value,'new_value':new_value})
    if modified_fields:
        fields=modified_fields
        recipient_email= instance.user.email
        recipient_name= instance.user.first_name + ' ' + instance.user.last_name
        code_email="MODFI"
        id_template_mailjet= Email_Mailjet.objects.get(code_email=code_email, lang_email=instance.lang_com).id_mailjet_email
        user_first_name = instance.user.first_name    
        vars ={'fields':fields ,'user_first_name':user_first_name}
        send_email_mailjet.delay(recipient_email, recipient_name,  id_template_mailjet, vars)
        
###################################################################################################
# Signal permettant de faire la traduction automatique des centres d'intérêts

@receiver(post_save, sender=InterestCenter)
def translate_centre_interet(sender, instance, created, **kwargs):
    if created:
        translator = deepl.Translator(settings.DEEPL_API_KEY)
        for lang_code in settings.LANGUAGES:
            if lang_code != settings.LANGUAGE_CODE:
                lang = lang_code[0]
                translated_text = translator.translate_text(instance.interest_center, target_lang=lang_code[0].upper())
                if "-" in lang:
                            lang=lang.replace("-", "_")
                setattr(instance, f"interest_center_{lang}", translated_text.text)
        instance.save()
        