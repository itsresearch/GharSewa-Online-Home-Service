# homeservices/admin.py

from django.contrib import admin
from .models import ServiceBooking

# admin.site.register(Service)
# admin.site.register(SubService)
admin.site.register(ServiceBooking)
