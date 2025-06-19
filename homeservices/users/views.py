from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from allauth.socialaccount.models import SocialAccount
from .forms import CustomUserCreationForm, LoginForm, ContactForm, TestimonialForm, UserRegistrationForm, ServiceRequestForm, ProfileEditForm
from .models import Testimonial
from service_providers.models import ServiceProvider, ServiceRequest, ServiceType
from service_providers.forms import ServiceProviderRegistrationForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.templatetags.static import static
from allservices.models import ServiceBooking
from itertools import chain
from django.db.models import Q

def index(request):
    testimonials = Testimonial.objects.all().order_by('-created_at')[:4]  # Fetch latest 4 testimonials
    return render(request, 'index.html', {'testimonials': testimonials})

def home(request):
    return render(request, 'users/home.html')

def select_login_type(request):
    return render(request, 'registration/select_login_type.html')

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'user')  # Default to regular user
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Check if user is a social account user
            is_social_user = SocialAccount.objects.filter(user=user).exists()
            
            # Explicitly set the authentication backend
            if is_social_user:
                user.backend = 'allauth.account.auth_backends.AuthenticationBackend'
            else:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            # Check if user is staff/admin
            if user.is_staff:
                login(request, user)
                return redirect('user_dashboard')  # Redirect to custom admin dashboard
            
            # Check if user is a service provider
            is_provider = ServiceProvider.objects.filter(user=user).exists()
            
            if user_type == 'provider':
                if is_provider:
                    if not user.serviceprovider.is_verified:
                        messages.warning(request, 'Please verify your email before logging in.')
                        logout(request)
                        return redirect('login')
                    login(request, user)
                    return redirect('provider_dashboard')
                else:
                    messages.error(request, 'This account is not registered as a service provider.')
                    logout(request)
                    return redirect('login')
            else:  # Regular user
                if is_provider:
                    messages.error(request, 'Please use the service provider login option.')
                    logout(request)
                    return redirect('login')
                login(request, user)
                return redirect('index')
        else:
            messages.error(request, 'Invalid email or password.')
    
    # Check if this is a provider login attempt
    user_type = request.GET.get('user_type', request.POST.get('user_type', 'user'))
    if user_type == 'provider':
        return render(request, 'registration/provider_login.html')
    return render(request, 'registration/login.html')

def select_signup_type(request):
    return render(request, 'registration/select_signup_type.html')

@csrf_protect
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def provider_signup(request):
    if request.method == 'POST':
        form = ServiceProviderRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Please check your email to verify your account.')
            return redirect('login')
    else:
        form = ServiceProviderRegistrationForm()
    return render(request, 'service_providers/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            full_message = f"Message from {name} <{email}>:\n\n{message}"

            send_mail(
                subject,
                full_message,
                email,
                ['researchofficial55@gmail.com'],  # receiver
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})


def about(request):
    return render(request, 'about.html')

def service(request):
    return render(request, 'service.html')

def team(request):
    return render(request, 'team.html')

def testimonial(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to submit a testimonial.')
            return redirect('login')
        
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.user = request.user
            testimonial.save()
            messages.success(request, 'Your testimonial has been submitted successfully!')
            return redirect('testimonial')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
        form = TestimonialForm(initial=initial_data)

    testimonials = Testimonial.objects.all().order_by('-created_at')
    return render(request, 'testimonial.html', {'form': form, 'testimonials': testimonials})

def appointment(request):
    return render(request, 'appointment.html')

def feature(request):
    return render(request, 'feature.html')

def contact(request):
    return render(request, 'contact.html')

def painting(request):
    return render(request, 'service/painting.html')

def plastering(request):
    return render(request, 'service/plastering.html')

def electrical(request):
    return render(request, 'service/electrical.html')

def plumbing(request):
    return render(request, 'service/plumbing.html')

def carpentry(request):
    return render(request, 'service/carpentry.html')

def flooring(request): 
    return render(request, 'service/flooring.html')

def roofing(request):
    return render(request, 'service/roofing.html')

def cleaning(request):
    return render(request, 'service/cleaning.html')

def appliance(request):
    return render(request, 'service/appliance.html')

def user_signup(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Explicitly authenticate and login with ModelBackend
            backend = ModelBackend()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, 'Welcome to GharSewa! Your account has been created successfully.')
            return redirect('index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/signup.html', {
        'form': form,
        'title': 'Sign Up as User',
        'submit_text': 'Create Account'
    })

@login_required
def user_home(request):
    # Get user's service requests
    service_requests = ServiceRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Initialize the service booking form
    form = ServiceRequestForm()
    
    return render(request, 'users/home.html', {
        'service_requests': service_requests,
        'form': form
    })

@login_required
def book_service(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.user = request.user
            service_request.status = 'pending'
            service_request.save()
            
            # Create notifications for service providers
            from service_providers.models import Notification
            Notification.create_service_request_notification(service_request)
            
            messages.success(request, 'Service request submitted successfully! Providers will be notified.')
            return redirect('service_requests')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    return redirect('service_requests')

@login_required
def profile_view(request):
    # Get the user instance
    user = request.user
    
    # Check if user is authenticated via social account
    is_social = hasattr(user, 'socialaccount_set') and user.socialaccount_set.exists()
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            
            # If social user, preserve their social account data
            if is_social:
                social_account = user.socialaccount_set.first()
                if social_account:
                    extra_data = social_account.extra_data
                    if not user.name and extra_data.get('name'):
                        user.name = extra_data['name']
                    if not user.profile_photo and extra_data.get('picture'):
                        user.profile_photo = extra_data['picture']
            
            user.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=user)
    
    # Get user's service requests
    service_requests = ServiceRequest.objects.filter(
        user=user
    ).order_by('-created_at')
    
    return render(request, 'users/profile.html', {
        'user': user,
        'form': form,
        'is_social': is_social,
        'service_requests': service_requests
    })

@login_required
def edit_profile(request):
    # Get the user instance
    user = request.user
    
    # Check if user is authenticated via social account
    is_social = hasattr(user, 'socialaccount_set') and user.socialaccount_set.exists()
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            
            # If social user, preserve their social account data
            if is_social:
                social_account = user.socialaccount_set.first()
                if social_account:
                    extra_data = social_account.extra_data
                    if not user.name and extra_data.get('name'):
                        user.name = extra_data['name']
                    if not user.profile_photo and extra_data.get('picture'):
                        user.profile_photo = extra_data['picture']
            
            user.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=user)
    
    return render(request, 'users/edit_profile.html', {
        'form': form,
        'is_social': is_social
    })

@login_required
def settings_view(request):
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Handle notification preferences
            notification_prefs = request.POST.getlist('notification_preferences')
            user.notification_preferences = {pref: True for pref in notification_prefs}
            
            user.save()
            messages.success(request, 'Your settings have been updated successfully!')
            return redirect('settings')
    else:
        form = UserSettingsForm(instance=request.user)
        
        # Pre-select current notification preferences
        if request.user.notification_preferences:
            form.initial['notification_preferences'] = [
                k for k, v in request.user.notification_preferences.items() if v
            ]
    
    return render(request, 'users/settings.html', {
        'form': form
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            request.user.delete()
            messages.success(request, 'Your account has been deleted.')
            return redirect('index')
        else:
            messages.error(request, 'Incorrect password.')
            return redirect('profile')
    return redirect('profile')

@login_required
def service_requests(request):
    # Get both types of service requests
    from allservices.models import ServiceBooking
    from itertools import chain
    from django.db.models import Q
    
    # Get service requests from both models
    service_requests = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    service_bookings = ServiceBooking.objects.filter(user=request.user).order_by('-created_at')
    
    # Combine the requests into a single list and sort by created_at
    all_requests = sorted(
        chain(service_requests, service_bookings),
        key=lambda x: x.created_at,
        reverse=True
    )
    
    # Get unique service types from both models
    service_types = set(
        list(ServiceRequest.objects.filter(user=request.user).values_list('service_type', flat=True).distinct()) +
        list(ServiceBooking.objects.filter(user=request.user).values_list('service', flat=True).distinct())
    )
    
    return render(request, 'users/service_requests.html', {
        'service_requests': all_requests,
        'service_types': service_types
    })

@login_required
def view_request(request, request_id):
    # Try to get ServiceRequest first
    try:
        request_obj = ServiceRequest.objects.get(id=request_id, user=request.user)
    except ServiceRequest.DoesNotExist:
        # If not found, try ServiceBooking
        try:
            from allservices.models import ServiceBooking
            request_obj = ServiceBooking.objects.get(id=request_id, user=request.user)
        except ServiceBooking.DoesNotExist:
            messages.error(request, 'Service request not found.')
            return redirect('service_requests')
    
    return render(request, 'users/request_detail.html', {
        'request_obj': request_obj
    })

@login_required
def cancel_request(request, request_id):
    if request.method == 'POST':
        # Try to get and cancel ServiceRequest first
        try:
            service_request = ServiceRequest.objects.get(id=request_id, user=request.user, status='pending')
            service_request.status = 'cancelled'
            service_request.save()
            
            # Delete associated notifications
            Notification.objects.filter(service_request=service_request).delete()
            
            messages.success(request, 'Service request cancelled successfully.')
        except ServiceRequest.DoesNotExist:
            # If not found, try ServiceBooking
            try:
                from allservices.models import ServiceBooking
                service_request = ServiceBooking.objects.get(id=request_id, user=request.user, status='pending')
                
                # Store provider info before cancellation
                provider = service_request.provider
                
                # Cancel the request
                service_request.status = 'cancelled'
                service_request.save()
                
                # If there was a provider assigned, notify them
                if provider:
                    from service_providers.models import Notification
                    Notification.objects.create(
                        provider=provider,
                        message=f'Service request from {service_request.user.get_full_name()} has been cancelled.',
                        notification_type='cancellation'
                    )
                
                messages.success(request, 'Service request cancelled successfully.')
            except ServiceBooking.DoesNotExist:
                messages.error(request, 'Service request not found or cannot be cancelled.')
    
    # Check if we should redirect to detail page or list page
    next_page = request.GET.get('next', 'service_requests')
    return redirect(next_page)