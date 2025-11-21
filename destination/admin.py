from django.contrib import admin

from destination.models import Destination, Destination_data, Destination_flux

admin.site.register(Destination)
admin.site.register(Destination_data)
admin.site.register(Destination_flux)