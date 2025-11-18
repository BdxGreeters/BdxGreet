from core.translator import translate
from django.conf import settings
from celery import shared_task
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist


# Traduction d'un champ

@shared_task
def translation_content(app_label,model_name, object_id, field_name):
    try:
        Model = apps.get_model(app_label,model_name)
        objet = Model.objects.get(pk=object_id)
        print(objet)
    except (LookupError, ObjectDoesNotExist) as e:
        raise ValueError(f"Erreur : {e}")

    for lang_code in settings.LANGUAGES:
        lang = lang_code[0]
        original_text = getattr(objet, field_name)
        translated_text = translate(original_text, target_lang=lang_code[0].upper())
        if "-" in lang:
            lang = lang.replace("-", "_")
        setattr(objet, f"{field_name}_{lang}", translated_text)

    objet.save()


###################################################################################################
# Traduction d'un champ avec des items

@shared_task
def translation_content_items(app_label,model_name, objet_id, nom_champ):
    print(app_label)
    print(model_name)
    print(objet_id)
    print(nom_champ)
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError:
        raise LookupError(f"Le modèle {model_name} dans l'application {app_label} n'existe pas.")
    try:
        objet = Model.objects.get(pk=objet_id)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist(f"L'objet avec l'ID {objet_id} n'existe pas dans le modèle {model_name}.") 
    # Récupérer la valeur du champ
    original_value = getattr(objet, nom_champ)
    # Si la valeur n'est pas None ou vide
    if original_value:
        # Séparer les items par virgule et nettoyer les espaces
        items = [item.strip() for item in original_value.split(",") if item.strip()]

        for lang_code in settings.LANGUAGES:
            lang = lang_code[0]
            # Traduire chaque item individuellement
            translated_items = []
            for item in items:
                translated_item = translate(item, target_lang=lang_code[0].upper())
                translated_items.append(translated_item)

            # Reconstruire la chaîne traduite
            translated_text = ", ".join(translated_items)

            # Gérer le format de la langue (remplacer '-' par '_')
            if "-" in lang:
                lang = lang.replace("-", "_")

            # Définir l'attribut traduit sur l'objet
            setattr(objet, f"{nom_champ}_{lang}", translated_text)

        # Sauvegarder l'objet
        objet.save()
###################################################################################################
# Fonction d'appel à un template Mailjet

from mailjet_rest import Client



@shared_task
def send_email_mailjet (recipient_email,recipient_name, template_mailjet_id, vars):
    template_id = template_mailjet_id
    mailjet = Client (auth=(settings.MAILJET_API_KEY,settings.MAILJET_SECRET_KEY),version='v3.1')
    data = {
        'Messages':[
            {
                'From':None,
                'TO' : [
                    {
                        'Email':recipient_email,
                        'Name' : recipient_name,
                    }
                ],             
                'TemplateID' : template_id,
                'TemplateLanguage' : True,
                'Variables': vars
            }
        ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code
 ##################################################################################################
 # Fonctio d'envoi de creation d'un utilisateur

from django.contrib.sites.shortcuts import get_current_site
from django.dispatch import receiver
from django.db.models.signals import post_save
from users.models import CustomUser

def envoyer_email_creation_utilisateur(user, request):
    current_site = get_current_site(request)
    code_email = "SETPW"
    try:
        from .models import Email_Mailjet
        id_template_mailjet = Email_Mailjet.objects.get(
            code_email=code_email,
            lang_email=user.lang_com
        ).id_mailjet_email
        reset_password(user.id, current_site, id_template_mailjet)
        print(f"(Nouvel utilisateur créé sur le domaine : {current_site.domain})")
    except Email_Mailjet.DoesNotExist:
        print(f"Template Mailjet non trouvé pour le code {code_email} et la langue {user.lang_com}.")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

###################################################################################################
# Fonction permettant d'initialiser ou réinitialiser le mot de passe

from users.models import CustomUser
from core.models import Email_Mailjet
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from core.tasks import send_email_mailjet
from django.utils.translation import gettext_lazy as _


def reset_password (user_id, domain, template_mailjet_id):
    template_mailjet_id = template_mailjet_id
    user = CustomUser.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    creation_link = f"http://{domain}{path}"
    recipient_email= user.email
    recipient_name =user.first_name + ' ' + user.last_name
    vars ={'url_password': creation_link,'user_first_name' : user.first_name}
    send_email_mailjet.delay(recipient_email, recipient_name,template_mailjet_id, vars)
###################################################################################################

