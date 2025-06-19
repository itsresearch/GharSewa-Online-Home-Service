from django import forms
from django.contrib.auth.forms import UserChangeForm
from users.models import CustomUser

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'name', 'first_name', 'last_name', 'profile_photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
        if 'password' in self.fields:
            del self.fields['password']