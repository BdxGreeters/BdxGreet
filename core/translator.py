
from deepl.exceptions import TooManyRequestsException
import time
from django.conf import settings
import deepl

print(settings.DEEPL_API_KEY)
translator = deepl.DeepLClient(settings.DEEPL_API_KEY)
def translate(text, target_lang,retries=5, delay=2):
    for attempt in range(retries):
        try:
            translate=translator.translate_text(text, target_lang=target_lang)
            return translate.text
        except TooManyRequestsException:
            print(f"Erreur 429 trop de requêtes. Attente de {delay} secondes....")
            time.sleep(delay)
            delay *= 2
    raise Exception("Echec de la traduction après plusieurs tentatives.")
