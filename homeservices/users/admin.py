# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .forms import CustomUserCreationForm

admin.site.site_header = "GharSewa Admin"
admin.site.site_title = "GharSewa Admin Portal"
admin.site.index_title = "Welcome to GharSewa Admin Dashboard"

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm  # Use our custom form for adding users
    model = CustomUser
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'first_name', 'last_name', 'profile_photo', 'profile_photo_preview')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )
    
    list_display = ('email', 'name', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'name', 'first_name', 'last_name')
    ordering = ('email',)
    
    readonly_fields = ('profile_photo_preview',)
    
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" width="150" style="border-radius:50%" /></a>', 
                obj.profile_photo
            )
        return "No photo"
    profile_photo_preview.short_description = 'Profile Photo Preview'

admin.site.register(CustomUser, CustomUserAdmin)