from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib.auth import login

class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        # Prevent Django Allauth from setting a username
        return None

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Handle social login before the user is redirected
        """
        # Check if user already exists
        User = get_user_model()
        email = sociallogin.user.email
        if email:
            try:
                user = User.objects.get(email=email)
                # If user exists, connect the social account and log them in
                if not sociallogin.is_existing:
                    sociallogin.connect(request, user)
                # Log the user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('index')
            except User.DoesNotExist:
                pass

    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social account.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get data from Google
        account_data = sociallogin.account.extra_data
        
        # Set user fields
        if account_data.get('name'):
            name_parts = account_data['name'].split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.name = account_data['name']
        
        if account_data.get('email'):
            user.email = account_data['email']
        
        if account_data.get('picture'):
            # Note: You might want to download and save the picture later
            user.profile_photo = account_data['picture']
        
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        If email exists, don't allow auto signup.
        """
        email = sociallogin.user.email
        User = get_user_model()
        if email and User.objects.filter(email=email).exists():
            return False
        return True
