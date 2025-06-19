from django.contrib import admin
from .models import ServiceType, ServiceProvider, ServiceRequest

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'service_type', 'location', 'is_verified', 'created_at')
    list_filter = ('service_type', 'is_verified', 'created_at')
    search_fields = ('name', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_type', 'status', 'provider', 'created_at')
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = ('user__email', 'location', 'description')
    readonly_fields = ('created_at', 'updated_at') 