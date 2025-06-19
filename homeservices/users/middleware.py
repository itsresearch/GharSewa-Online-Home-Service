from django.shortcuts import redirect
from django.urls import resolve, reverse
from service_providers.models import ServiceProvider
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.conf import settings

class UserTypeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_url = resolve(request.path_info).url_name
            
            # Check if user is a service provider
            try:
                provider = ServiceProvider.objects.get(user=request.user)
                is_provider = True
            except ServiceProvider.DoesNotExist:
                is_provider = False

            # If user is a service provider trying to access user edit profile
            if is_provider and current_url == 'edit_profile':
                return redirect('provider_edit_profile')
            
            # If regular user trying to access provider edit profile
            if not is_provider and current_url == 'provider_edit_profile':
                return redirect('edit_profile')

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if view has login_required decorator
        if getattr(view_func, 'login_required', False):
            if not request.user.is_authenticated:
                # Get the login url
                resolved_login_url = reverse(settings.LOGIN_URL)
                
                # Get the next parameter
                path = request.get_full_path()
                
                # Redirect to login page with next parameter
                return redirect_to_login(
                    path,
                    resolved_login_url,
                    REDIRECT_FIELD_NAME
                ) 