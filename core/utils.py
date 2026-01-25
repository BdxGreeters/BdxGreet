# Identifiant unique pour les fichiers uploadés
import os
import uuid
from django.db import models
from django.utils.timezone import now
from django.utils.text import slugify

import os
import uuid
from django.utils.timezone import now

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    
    # 1. Récupérer le nom du modèle (ex: destination)
    model_name = instance.__class__.__name__.lower()
    
    # 2. Trouver le nom du champ (ex: logo_dest)
    # On cherche quel champ de l'instance possède le fichier correspondant au nom actuel
    field_name = "file" # Valeur par défaut
    for field in instance._meta.fields:
        # On vérifie si c'est un champ de fichier et si son nom correspond
        if hasattr(getattr(instance, field.name), 'name'):
            if getattr(instance, field.name).name == filename:
                field_name = field.name
                break

    # 3. Nettoyer le nom du champ (enlever les suffixes comme _dest ou _img si vous voulez)
    # Exemple : logo_dest -> logo
    clean_field_name = field_name.replace('_dest', '').replace('_img', '').replace('_photo', '')

    # 4. Générer le nom final : champ_modele_uuid.ext
    # Exemple : logo_destination_a1b2c3d4e5.jpg
    new_filename = f"{clean_field_name}_{model_name}_{uuid.uuid4().hex[:10]}.{ext}"
    
    # Organiser par date dans le dossier uploads
    return os.path.join(f"uploads/{now().strftime('%Y/%m')}/", new_filename)

###################################################################################################
