from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import ServiceProvider, ServiceType
import re
import imghdr

class ServiceProviderRegistrationForm(UserCreationForm):
    name = forms.CharField(
        max_length=100,
        error_messages={'required': 'Please enter your name'}
    )
    age = forms.IntegerField(
        min_value=18,
        max_value=100,
        error_messages={
            'required': 'Please enter your age',
            'min_value': 'You must be at least 18 years old',
            'max_value': 'Age cannot be more than 100'
        }
    )
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Please enter your email',
            'invalid': 'Please enter a valid email address'
        }
    )
    phone = forms.CharField(
        max_length=15,
        error_messages={
            'required': 'Please enter your phone number',
            'invalid': 'Please enter a valid phone number'
        }
    )
    location = forms.CharField(
        max_length=200,
        error_messages={'required': 'Please enter your location'}
    )
    service_type = forms.ModelChoiceField(
        queryset=ServiceType.objects.all(),
        empty_label="Select a service type",
        error_messages={'required': 'Please select a service type'}
    )
    profile_photo = forms.ImageField(
        required=False,
        error_messages={'invalid': 'Please upload a valid image file (JPEG, PNG, or GIF)'},
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif'
        })
    )
    available_days = forms.MultipleChoiceField(
        choices=ServiceProvider.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        error_messages={'required': 'Please select at least one available day'}
    )

    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'password1', 'password2', 'age', 
                 'phone', 'location', 'service_type', 'profile_photo', 'available_days')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            raise forms.ValidationError('Please enter a valid phone number (9-15 digits)')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered')
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            # Get the file extension
            ext = photo.name.split('.')[-1].lower()
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            
            if ext not in valid_extensions:
                raise forms.ValidationError('Please upload a valid image file (JPEG, PNG, or GIF)')
            
            # Check file size (5MB limit)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file size must be less than 5MB')
            
            try:
                # Try to verify the file is actually an image
                image_type = imghdr.what(photo)
                if image_type not in ['jpeg', 'png', 'gif']:
                    raise forms.ValidationError('The uploaded file is not a valid image')
            except Exception:
                raise forms.ValidationError('The uploaded file is not a valid image')
                
        return photo

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['name']
        
        if commit:
            user.save()
            service_provider = ServiceProvider.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                age=self.cleaned_data['age'],
                phone=self.cleaned_data['phone'],
                location=self.cleaned_data['location'],
                service_type=self.cleaned_data['service_type'],
                profile_photo=self.cleaned_data.get('profile_photo'),
                available_days=','.join(self.cleaned_data['available_days'])
            )
        return user

class ServiceProviderProfileForm(forms.ModelForm):
    available_days = forms.MultipleChoiceField(
        choices=ServiceProvider.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )

    class Meta:
        model = ServiceProvider
        fields = ('name', 'age', 'phone', 'location', 'service_type', 
                 'profile_photo', 'available_days')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'service_type': forms.Select(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['available_days'].initial = self.instance.available_days.split(',') 