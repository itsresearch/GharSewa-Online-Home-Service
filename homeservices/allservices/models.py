from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Define service types at module level to ensure consistency
SERVICE_TYPES = (
    ('cleaning', 'Cleaning'),
    ('painting', 'Painting'),
    ('wall-painting', 'Wall Painting'),
    ('exterior-painting', 'Exterior Painting'),
    ('ceiling-painting', 'Ceiling Painting'),
    ('touch-up', 'Touch Up'),
    ('roofing', 'Roofing'),
    ('electrical', 'Electrical'),
    ('flooring', 'Flooring'),
    ('wooden-flooring', 'Wooden Flooring'),
    ('plastering', 'Plastering'),
    # Plumbing Services
    ('plumbing', 'Plumbing'),
    ('bathroom-fixtures', 'Bathroom Fixtures'),
    ('sewer-line-repair', 'Sewer Line Repair'),
    ('pipe-repair', 'Pipe Repair'),
    ('drain-cleaning', 'Drain Cleaning'),
    ('water-heater-service', 'Water Heater Service'),
    ('water-heater-installation', 'Water Heater Installation'),
    ('water-heater-repair', 'Water Heater Repair'),
    ('faucet-repair', 'Faucet Repair'),
    ('toilet-repair', 'Toilet Repair'),
    ('sink-installation', 'Sink Installation'),
    ('leak-repair', 'Leak Repair'),
    ('pipe-installation', 'Pipe Installation'),
    # Appliance Services
    ('appliance', 'Appliance'),
    ('washing-machine', 'Washing Machine'),
    ('water-heater', 'Water Heater'),
    ('gardening', 'Gardening'),
)

# Define service type categories for better matching
SERVICE_CATEGORIES = {
    'plumbing': [
        'plumbing', 'bathroom-fixtures', 'sewer-line-repair', 'pipe-repair',
        'drain-cleaning', 'water-heater-service', 'water-heater-installation',
        'water-heater-repair', 'faucet-repair', 'toilet-repair', 'sink-installation',
        'leak-repair', 'pipe-installation'
    ],
    'painting': [
        'painting', 'wall-painting', 'exterior-painting', 'ceiling-painting', 'touch-up'
    ],
    'flooring': ['flooring', 'wooden-flooring'],
    'appliance': ['appliance', 'washing-machine', 'water-heater'],
    'electrical': ['electrical'],
    'roofing': ['roofing'],
    'plastering': ['plastering'],
    'cleaning': ['cleaning'],
    'gardening': ['gardening']
}

class ServiceBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='service_bookings', null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    service = models.CharField(max_length=50, choices=SERVICE_TYPES)
    preferred_date = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider = models.ForeignKey('ServiceProvider', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.service} ({self.status})"

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def get_service_category(service_type):
        """Get the main category for a service type"""
        service_type = service_type.lower()
        for category, services in SERVICE_CATEGORIES.items():
            if service_type in services:
                return category
        return service_type

class ServiceProvider(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='allservices_provider',
        null=True,  # Keep nullable for existing records
        blank=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    age = models.PositiveIntegerField()
    service_type = models.CharField(max_length=100, choices=SERVICE_TYPES)
    photo = models.ImageField(upload_to='provider_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.user:
            self.email = self.user.email
        if self.service_type:
            self.service_type = self.service_type.lower()
        super().save(*args, **kwargs)

    def get_related_services(self):
        """Get all service types that this provider can handle"""
        main_category = ServiceBooking.get_service_category(self.service_type)
        return SERVICE_CATEGORIES.get(main_category, [main_category])

    class Meta:
        unique_together = ('user',)  # Ensure one provider per user