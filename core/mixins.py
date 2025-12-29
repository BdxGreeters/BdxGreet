from django import forms
from django.utils.safestring import mark_safe

from core.tasks import translation_content

# Affichage des Help_text

class HelpTextTooltipMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            help_text = field.help_text
            if help_text:
                field.help_text = None
                # Ajouter une icône Bootstrap avec tooltip dans le label
                tooltip_html = f'''
                    <span data-bs-toggle="tooltip" title="{help_text}" style="cursor: help;">
                        <i class="bi bi-info-circle" style="margin-left: 10px;"></i>
                    </span>
                '''
                field.label = mark_safe(f"{field.label}{tooltip_html}")

###################################################################################################

# Ajout à une liste dans un champ Texte

class CommaSeparatedFieldMixin:
    comma_fields_config = {}  # Exemple : {'list_experience_cluster': {'min': 1, 'max': 5}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.comma_fields_config:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'comma-input-field',
                    'data-field-name': field_name,
                    'data-min-items': self.comma_fields_config[field_name].get('min', 0),
                    'data-max-items': self.comma_fields_config[field_name].get('max', 10),
                })



    def clean(self):
        cleaned_data = super().clean()
        for field_name, config in self.comma_fields_config.items():
            value = cleaned_data.get(field_name, "")
            items = [item.strip() for item in value.split(",") if item.strip()]
            min_items = config.get('min', 0)
            max_items = config.get('max', 10)
            if len(items) < min_items:
                self.add_error(field_name, f"Minimum {min_items} éléments requis.")
            elif len(items) > max_items:
                self.add_error(field_name, f"Maximum {max_items} éléments autorisés.")
            else:
                cleaned_data[field_name] = ",".join(items)
        return cleaned_data

###################################################################################################

#Champs éditables selon les groupes d'utilisateurs

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from core.models import FieldPermission


class FieldPermissionMixin:
    """
    Mixin pour gérer les permissions de champs pour un objet donné,
    avec support pour une liste de groupes et une relation ManyToManyField.
    """
    permission_groups = []  # Liste des groupes autorisés à définir les permissions
    target_group_name = None  # Groupe cible qui reçoit les permissions
    app_name = None  # Nom de l'application

    def user_has_any_permission_group(self, user):
        """
        Vérifie si l'utilisateur appartient à au moins un des groupes dans permission_groups.
        """
        if not self.permission_groups:
            raise ValueError("La liste des groupes de permission est vide.")

        user_groups = user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in self.permission_groups)

    def get_field_permissions(self, obj):
        """
        Récupère les permissions de champs pour un objet donné,
        en filtrant par le groupe cible.
        """
        if not self.target_group_name:
            raise ValueError("Le nom du groupe cible n'est pas défini.")

        target_group = get_object_or_404(Group, name=self.target_group_name)
        content_type = ContentType.objects.get_for_model(obj)
        permissions = FieldPermission.objects.filter(
            content_type=content_type,
            object_id=obj.id,
            app_name=self.app_name,
            target_group=target_group  # Filtrer par le groupe cible
        )
        return {p.field_name: p.is_editable for p in permissions}

    def update_field_permissions(self, obj, form):
        """
        Met à jour les permissions de champs pour un objet donné,
        en gérant la relation ManyToManyField pour les groupes.
        """
        if not self.permission_groups or not self.target_group_name:
            raise ValueError("Les groupes de permission ou le groupe cible ne sont pas définis.")

        # Récupérer les groupes de permission et le groupe cible
        permission_group_objs = [get_object_or_404(Group, name=group) for group in self.permission_groups]
        target_group = get_object_or_404(Group, name=self.target_group_name)

        content_type = ContentType.objects.get_for_model(obj)

        for field_name in form.editable_fields:
            is_editable = form.cleaned_data.get(f'can_edit_{field_name}', True)

            # Mettre à jour ou créer la permission
            field_permission, created = FieldPermission.objects.update_or_create(
                field_name=field_name,
                content_type=content_type,
                object_id=obj.id,
                app_name=self.app_name,
                target_group=target_group,
                defaults={'is_editable': is_editable}
            )

            # Gérer la relation ManyToManyField pour les groupes
            if created:
                field_permission.group.set(permission_group_objs)
            else:
                # Ajouter les groupes manquants
                for group in permission_group_objs :
                    if group not in field_permission.group.all():
                        field_permission.group.add(group)

###################################################################################################
# Mixin Gestion des permissions des champs définis éditables dans un formulaire

class FormFieldPermissionMixin:
    """
    Mixin pour gérer les permissions de champs basées sur la configuration
    fournie par un formulaire (attribut editable_fields).
    """
    permission_groups = []  # Groupes autorisés à modifier les permissions (ex: ['SuperAdmin'])
    target_group_name = None  # Groupe cible (ex: 'Admin')
    app_name = None

    def user_has_any_permission_group(self, user):
        """
        Vérifie si l'utilisateur appartient à au moins un des groupes dans permission_groups.
        """
        if not self.permission_groups:
            raise ValueError("La liste des groupes de permission est vide.")

        user_groups = user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in self.permission_groups)

    def get_field_permissions(self, obj):
        """
        Récupère les permissions de champs pour un objet donné,
        en filtrant par le groupe cible.
        """
        if not self.target_group_name:
            raise ValueError("Le nom du groupe cible n'est pas défini.")

        target_group = get_object_or_404(Group, name=self.target_group_name)
        content_type = ContentType.objects.get_for_model(obj)
        permissions = FieldPermission.objects.filter(
            content_type=content_type,
            object_id=obj.id,
            app_name=self.app_name,
            target_group=target_group  # Filtrer par le groupe cible
        )
        return {p.field_name: p.is_editable for p in permissions}


    def update_permissions_from_form(self, obj, form):
        if not self.target_group_name or not self.app_name:
            raise ValueError("target_group_name et app_name doivent être définis.")

        target_group = get_object_or_404(Group, name=self.target_group_name)
        permission_group_objs = list(Group.objects.filter(name__in=self.permission_groups))
        content_type = ContentType.objects.get_for_model(obj)
        
        # Liste des champs actuellement définis dans le formulaire
        current_editable_fields = getattr(form, 'editable_fields', [])

        # 1. NETTOYAGE : Supprimer les permissions qui ne sont plus dans editable_fields
        FieldPermission.objects.filter(
            content_type=content_type,
            object_id=obj.id,
            target_group=target_group,
            app_name=self.app_name
        ).exclude(field_name__in=current_editable_fields).delete()

        # 2. MISE À JOUR / CRÉATION
        for field_name in current_editable_fields:
            permission_key = f'can_edit_{field_name}'
            # On récupère la valeur, par défaut False si absent
            is_editable = form.cleaned_data.get(permission_key, False)

            field_permission, created = FieldPermission.objects.update_or_create(
                field_name=field_name,
                content_type=content_type,
                object_id=obj.id,
                app_name=self.app_name,
                target_group=target_group,
                defaults={'is_editable': is_editable}
            )
            
            if permission_group_objs:
                field_permission.group.set(permission_group_objs)

###################################################################################################

# Mixin pour gérer la création/mise à jour des modèles liés à un autre modèle par des champs CharFied

from django.forms import CharField

class RelatedModelsMixin:
    """

    Attributs requis dans la classe fille :
    - related_fields : dictionnaire {nom_champ_form: (Model, nom_champ_m2m,nomchamp Model)}
    """
    related_fields = {}  # À définir dans la vue du modèle de base

    def form_valid(self, form):
        response = super().form_valid(form)
        cluster = self.object

        for form_field, (model, m2m_field, model_attr) in self.related_fields.items():
            data_string = form.cleaned_data.get(form_field, "")
            if not data_string:
                continue

            names = [name.strip() for name in data_string.split(',') if name.strip()]
            objects = []
            for name in names:
                # 1. Récupération ou création de l'objet
                obj, created = model.objects.get_or_create(**{model_attr: name})
                
                # 2. Si l'objet est nouveau, on déclenche la traduction
                if created:
                    translation_content(
                        app_label=obj._meta.app_label,
                        model_name=obj._meta.model_name,
                        object_id=obj.pk,
                        field_name=model_attr
                    )
                    # On rafraîchit l'objet pour avoir les champs traduits en mémoire
                    obj.refresh_from_db()

                objects.append(obj)
            
            getattr(cluster, m2m_field).set(objects)

        return response
