# users/signals.py
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def populate_profile(request, user, sociallogin=None, **kwargs):
    if sociallogin and sociallogin.account.provider == 'google':
        extra_data = sociallogin.account.extra_data
        
        # Extract first and last names if available
        if 'given_name' in extra_data:
            user.first_name = extra_data['given_name']
        if 'family_name' in extra_data:
            user.last_name = extra_data['family_name']
        
        # Set the name field
        user.name = extra_data.get('name', '')
        
        # Ensure email is set (should be already)
        user.email = extra_data.get('email', user.email)
        
        # Profile photo
        picture = extra_data.get('picture')
        if picture:
            user.profile_photo = picture
        
        # Save all changes
        user.save()
