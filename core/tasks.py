from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from core.translator import translate

@shared_task(
    bind=True,
    max_retries=5,
    # Re-tente automatiquement pour ces erreurs spécifiques
    autoretry_for=(ObjectDoesNotExist, LookupError, Exception),
    # Augmente le temps d'attente entre chaque essai (2s, 4s, 8s, 16s...)
    retry_backoff=True, 
    retry_backoff_max=600, # Max 10 minutes d'attente
    retry_jitter=True      # Ajoute un léger délai aléatoire pour éviter les collisions
)
def translation_content(self, app_label, model_name, object_id, field_name):
    """
    Tâche Celery pour traduire un champ spécifique d'un modèle.
    Supporte les retries automatiques si la base de données n'est pas encore prête.
    """
    # 1. Récupération dynamique du modèle
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError as e:
        # Erreur critique de configuration : le modèle n'existe pas
        raise ValueError(f"Modèle {app_label}.{model_name} introuvable : {e}")

    # 2. Récupération de l'objet (déclenche autoretry si DoesNotExist)
    # C'est ici que l'erreur 'DoesNotExist' est capturée et transformée en retry
    objet = Model.objects.get(pk=object_id)

    # 3. Récupération du texte original
    original_text = getattr(objet, field_name, None)
    if not original_text:
        return f"Aucun texte à traduire pour {model_name} (ID: {object_id})"

    # 4. Boucle de traduction à travers les langues du projet
    for lang_code in settings.LANGUAGES:
        lang = lang_code[0]  # ex: 'en' ou 'fr-ca'
        
        # On ignore la langue source ou si la traduction est vide
        translated_text = translate(original_text, target_lang=lang.upper())
        
        if not translated_text:
            continue

        # 5. Préparation du nom du champ de destination (ex: name_en, name_fr_ca)
        lang_suffix = lang.replace("-", "_")
        target_field = f"{field_name}_{lang_suffix}"

        # 6. Mise à jour de l'attribut si le champ existe sur le modèle
        if hasattr(objet, target_field):
            setattr(objet, target_field, translated_text)

    # 7. Sauvegarde finale des traductions
    objet.save()
    
    return f"Traduction terminée avec succès pour {model_name} (ID: {object_id})"

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
 # Fonction d'envoi du courriel  de creation d'un utilisateur

from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model

User = get_user_model()

def envoyer_email_creation_utilisateur(user_id, request):
    # On récupère le domaine avant, car l'objet 'request' peut être difficile à 
    # manipuler une fois la vue terminée.
    domain = get_current_site(request).domain

    def send():
        try:
            # On récupère l'utilisateur à l'intérieur de send()
            # Cela garantit que la transaction est terminée et l'user est disponible
            user = User.objects.get(id=user_id)
            code_email = "SETPW"
            
            from .models import Email_Mailjet
            try:
                template = Email_Mailjet.objects.get(
                    code_email=code_email,
                    lang_email=user.lang_com
                )
                
                # Appel de votre fonction réelle de reset
                reset_password(user.id, domain, template.id_mailjet_email)
                print(f"Email mis en file d'attente pour {user.email}")
                
            except Email_Mailjet.DoesNotExist:
                print(f"Erreur : Template Mailjet '{code_email}' introuvable pour la langue '{user.lang_com}'")
                
        except User.DoesNotExist:
            print(f"Erreur : Utilisateur ID {user_id} introuvable lors de l'envoi du mail.")
        except Exception as e:
            print(f"Erreur critique lors de l'envoi de l'email : {e}")

    # Enregistre la fonction send pour exécution APRES le commit
    transaction.on_commit(send)
###################################################################################################
# Fonction permettant d'initialiser ou réinitialiser le mot de passe

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from core.models import Email_Mailjet
from core.tasks import send_email_mailjet
from users.models import CustomUser


def reset_password(user_id, domain, template_mailjet_id):
    user = CustomUser.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    
    # Utiliser le protocole correct (HTTPS si possible)
    protocol = 'http' if 'localhost' in domain or '127.0.0.1' in domain else 'https'
    creation_link = f"{protocol}://{domain}{path}"
    
    recipient_email = user.email
    recipient_name = f"{user.first_name} {user.last_name}"
    vars = {'url_password': creation_link, 'user_first_name': user.first_name}
    
    send_email_mailjet.delay(recipient_email, recipient_name, template_mailjet_id, vars)
###################################################################################################

