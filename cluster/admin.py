from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from cluster.models import Cluster

admin.site.register(Cluster)


