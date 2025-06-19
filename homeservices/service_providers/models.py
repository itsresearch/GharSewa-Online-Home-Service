from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone
from allservices.models import SERVICE_CATEGORIES

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class ServiceProvider(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)])
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=200)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='provider_photos/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    
    # Availability
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    available_days = models.CharField(max_length=100)  # Store as comma-separated values
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.service_type}"

    def get_service_category(self):
        """Get the main category for a service type"""
        service_type = self.service_type.name.lower()
        for category, services in SERVICE_CATEGORIES.items():
            if service_type in services:
                return category
        return service_type

    def get_related_services(self):
        """Get all service types that this provider can handle"""
        main_category = self.get_service_category()
        return SERVICE_CATEGORIES.get(main_category, [main_category])

class ServiceRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_requests')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    description = models.TextField()
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], default='pending')
    provider = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request by {self.user.username} for {self.service_type}"

class Notification(models.Model):
    provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_request = models.ForeignKey('ServiceRequest', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.provider.name}: {self.message[:50]}"

    @classmethod
    def create_service_request_notification(cls, service_request):
        """Create a notification for a new service request"""
        # Find all providers of the requested service type
        from .models import ServiceProvider
        providers = ServiceProvider.objects.filter(service_type=service_request.service_type)
        
        for provider in providers:
            cls.objects.create(
                provider=provider,
                message=f"New service request from {service_request.user.get_full_name() or service_request.user.username} in {service_request.location}",
                related_request=service_request
            )

    @classmethod
    def create_status_update_notification(cls, service_request):
        """Create a notification for service request status updates"""
        if service_request.provider:
            cls.objects.create(
                provider=service_request.provider,
                message=f"Service request from {service_request.user.get_full_name() or service_request.user.username} has been {service_request.status}",
                related_request=service_request
            ) 