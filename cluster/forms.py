from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div,Field, Fieldset, HTML, Hidden
from crispy_forms.bootstrap import InlineCheckboxes, InlineRadios,Tab, TabHolder
from core.mixins import HelpTextTooltipMixin, CommaSeparatedFieldMixin
from core.models import FieldPermission, Language_communication, Pays
from cluster.models import Cluster

User = get_user_model()

class ClusterForm(CommaSeparatedFieldMixin, HelpTextTooltipMixin, forms.ModelForm):
    editable_fields = [
        'code_cluster', 'name_cluster', 'statut_cluster', 'adress_cluster', 'desc_cluster',
        'paypal_cluster', 'admin_cluster', 'country_admin_cluster', 'admin_alt_cluster',
        'country_admin_alt_cluster', 'param_nbr_part_cluster', 'langs_com',
        'backup_mails_cluster', 'url_biblio_cluster', 'url_biblio_Greeter_cluster',
        'list_experience_cluster', 'profil_interet_cluster', 'reason_no_reply_greeter_cluster',
        'reason_no_reply_visitor_cluster', 'list_notoriety_cluster'
    ]

    class Meta:
        model = Cluster
        fields = [
            'code_cluster', 'name_cluster', 'statut_cluster', 'adress_cluster', 'desc_cluster',
            'paypal_cluster', 'admin_cluster', 'country_admin_cluster', 'admin_alt_cluster',
            'country_admin_alt_cluster', 'param_nbr_part_cluster', 'langs_com',
            'backup_mails_cluster', 'url_biblio_cluster', 'url_biblio_Greeter_cluster',
            'list_experience_cluster', 'profil_interet_cluster', 'reason_no_reply_greeter_cluster',
            'reason_no_reply_visitor_cluster', 'list_notoriety_cluster'
        ]
        widgets = {
            'admin_cluster': forms.Select(attrs={'class': 'form-select'}),
            'country_admin_cluster' : forms.Select(attrs={'class': 'form-select'}),
            'country_admin_alt_cluster' : forms.Select(attrs={'class': 'form-select'}),
            'admin_alt_cluster': forms.Select(attrs={'class': 'form-select'}),
            'statut_cluster': forms.RadioSelect(),
            'langs_com': forms.CheckboxSelectMultiple(),
            'desc_cluster': forms.Textarea(attrs={'rows': 2}),
        }

    comma_fields_config = {
        'list_experience_cluster': {'min': 2, 'max': 10},
        'list_notoriety_cluster': {'min': 2, 'max': 10},
        'reason_no_reply_visitor_cluster': {'min': 1, 'max': 10},
        'profil_interet_cluster': {'min': 1, 'max': 10},
        'reason_no_reply_greeter_cluster': {'min': 1, 'max': 10}
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Ajouter un champ BooleanField pour chaque champ éditable
        for field_name in self.editable_fields:
            self.fields[f'can_edit_{field_name}'] = forms.BooleanField(
                label="",
                required=False,
                initial=False,
            )

        # Masquer les cases à cocher si l'utilisateur n'est pas dans un groupe autorisé
        if self.user and not self.user.groups.filter(name__in=['SuperAdmin']).exists():
            for field_name in self.editable_fields:
                self.fields[f'can_edit_{field_name}'].widget = forms.HiddenInput()

        # Si l'utilisateur est autorisé et qu'on modifie un objet existant
        if self.user and self.user.groups.filter(name__in=['SuperAdmin']).exists() and self.instance and self.instance.pk:
            target_group = get_object_or_404(Group, name='Admin')
            content_type = ContentType.objects.get_for_model(self.instance)
            permissions = FieldPermission.objects.filter(
                content_type=content_type,
                object_id=self.instance.pk,
                target_group=target_group,
                app_name='cluster'
            )
            for field_name in self.editable_fields:
                permission = permissions.filter(field_name=field_name).first()
                if permission and permission.is_editable:
                    self.fields[f'can_edit_{field_name}'].initial = True

        # Filtrer les utilisateurs éligibles pour admin_cluster et admin_alt_cluster
        excluded_users = User.objects.filter(
            Q(admin_cluster__isnull=False) | Q(admin_alt_cluster__isnull=False)
        ).exclude(
            Q(admin_cluster=self.instance) | Q(admin_alt_cluster=self.instance)
        ).distinct() if self.instance and self.instance.pk else User.objects.filter(
            Q(admin_cluster__isnull=False) | Q(admin_alt_cluster__isnull=False)
        ).distinct()

        eligible_users = User.objects.filter(
            is_superuser=False,
        ).exclude(
            groups__name='Greeter'
        ).exclude(
            id__in=excluded_users
        )

        if self.instance and self.instance.pk:
            if self.instance.admin_cluster:
                eligible_users = eligible_users | User.objects.filter(pk=self.instance.admin_cluster.pk)
            if self.instance.admin_alt_cluster:
                eligible_users = eligible_users | User.objects.filter(pk=self.instance.admin_alt_cluster.pk)

        self.fields['admin_cluster'].queryset = eligible_users
        self.fields['admin_alt_cluster'].queryset = eligible_users

        # Initialiser les valeurs des champs admin_cluster et admin_alt_cluster
        if self.instance and self.instance.pk:
            self.fields['admin_cluster'].initial = self.instance.admin_cluster
            self.fields['admin_alt_cluster'].initial = self.instance.admin_alt_cluster

        self.fields['country_admin_cluster'].queryset = Pays.objects.all().order_by('nom_pays')
        self.fields['country_admin_alt_cluster'].queryset = Pays.objects.all().order_by('nom_pays')

        # Configuration du layout avec crispy_forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    _("Identification"),
                    Row(
                        Column('code_cluster', css_class='col-md-2'),
                        Column('name_cluster', css_class='col-md-6'),
                        Column('can_edit_name_cluster', css_class='col-md-1'),
                    ),
                    Row(
                        Column('adress_cluster', css_class='col-md-11'),
                        Column('can_edit_adress_cluster', css_class='col-md-1'),
                        Column(Field('desc_cluster'), css_class='col-md-11'),
                        Column('can_edit_desc_cluster', css_class='col-md-1'),
                    ),
                ),
                Tab(
                    _("Administration"),
                    Fieldset(
                        _("Administrateur principal"),
                        Row(
                            Column('admin_cluster', css_class='col-md-6'),
                            Column('can_edit_admin_cluster', css_class='col-md-1'),
                            Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_admin_cluster">{_("Nouvel utilisateur")}</button>'),
                                   css_class="d-flex align-items-center")
                        ),
                        Row(
                            Column('country_admin_cluster', css_class='col-md-4'),
                            Column('can_edit_country_admin_cluster', css_class='col-md-1'),
                        ),
                        css_class="fieldset-personnalise"
                    ),
                    Fieldset(
                        _("Administrateur alternatif"),
                        Row(
                            Column('admin_alt_cluster', css_class='col-md-6'),
                            Column('can_edit_admin_alt_cluster', css_class='col-md-1'),
                            Column(HTML(f'<button type="button" class="btn btn-sm btn-primary ms-2" data-target-field="id_admin_alt_cluster">{_("Nouvel utilisateur")}</button>'),
                                   css_class="d-flex align-items-center")
                        ),
                        Row(
                            Column('country_admin_alt_cluster', css_class='col-md-4'),
                            Column('can_edit_country_admin_alt_cluster', css_class='col-md-1'),
                        ),
                        css_class="fieldset-personnalise"
                    ),
                ),
                Tab(
                    _("Paramètres"),
                    Row(
                        Column(InlineRadios('statut_cluster', css_class='col-md-6')),
                        Column('can_edit_statut_cluster', css_class='col-md-1'),
                    ),
                    Row(
                        Column(InlineCheckboxes('langs_com', css_class='col-md-9')),
                        Column('can_edit_langs_com', css_class='col-md-1'),
                    ),
                    Row(
                        Column('param_nbr_part_cluster', css_class='col-md-3'),
                        Column('can_edit_param_nbr_part_cluster', css_class='col-md-1'),
                        Column('paypal_cluster', css_class='col-md-6'),
                        Column('can_edit_paypal_cluster', css_class='col-md-1'),
                        Column('backup_mails_cluster', css_class='col-md-6'),
                        Column('can_edit_backup_mails_cluster', css_class='col-md-1'),
                        Column('url_biblio_cluster', css_class='col-md-6'),
                        Column('can_edit_url_biblio_cluster', css_class='col-md-1'),
                        Column('url_biblio_Greeter_cluster', css_class='col-md-6'),
                        Column('can_edit_url_biblio_Greeter_cluster', css_class='col-md-1'),
                    ),
                ),
                Tab(
                    _("Listes"),
                    Row(
                        Column(Field('list_experience_cluster'), css_class='col-md-11'),
                        Column('can_edit_list_experience_cluster', css_class='col-md-1'),
                        Column('profil_interet_cluster', css_class='col-md-11'),
                        Column('can_edit_profil_interet_cluster', css_class='col-md-1'),
                        Column('reason_no_reply_greeter_cluster', css_class='col-md-11'),
                        Column('can_edit_reason_no_reply_greeter_cluster', css_class='col-md-1'),
                        Column('reason_no_reply_visitor_cluster', css_class='col-md-11'),
                        Column('can_edit_reason_no_reply_visitor_cluster', css_class='col-md-1'),
                        Column('list_notoriety_cluster', css_class='col-md-11'),
                        Column('can_edit_list_notoriety_cluster', css_class='col-md-1'),
                    ),
                ),
            ),
            Submit('submit', _("Enregistrer"), css_class='btn-primary')
        )

    def save(self, commit=True):
        cluster = super().save(commit=False)

        if commit:
            cluster.save()
            self.save_m2m()

            # Mettre à jour le code_cluster pour admin_cluster
            if self.cleaned_data.get('admin_cluster'):
                admin_user = self.cleaned_data['admin_cluster']
                admin_user.code_cluster = cluster.code_cluster
                admin_user.save()

            # Mettre à jour le code_cluster pour admin_alt_cluster
            if self.cleaned_data.get('admin_alt_cluster'):
                admin_alt_user = self.cleaned_data['admin_alt_cluster']
                admin_alt_user.code_cluster = cluster.code_cluster
                admin_alt_user.save()

        return cluster