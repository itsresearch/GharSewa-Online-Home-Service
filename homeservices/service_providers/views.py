from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login, authenticate
from django.template.loader import render_to_string
from django.utils import timezone
from functools import wraps
from .forms import ServiceProviderRegistrationForm, ServiceProviderProfileForm
from .models import ServiceProvider, ServiceRequest, ServiceType, Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from allservices.models import ServiceBooking, SERVICE_TYPES, SERVICE_CATEGORIES
from django.views.decorators.csrf import csrf_protect

def provider_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            if not provider.is_verified:
                # Just show a warning message but allow access
                messages.warning(request, 'Please verify your email to ensure full account functionality.')
            return view_func(request, *args, **kwargs)
        except ServiceProvider.DoesNotExist:
            messages.error(request, 'You must be registered as a service provider to access this page.')
            return redirect('provider_signup')
    return _wrapped_view

def provider_signup(request):
    if request.method == 'POST':
        form = ServiceProviderRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Generate verification token
            provider = ServiceProvider.objects.get(user=user)
            provider.email_verification_token = get_random_string(64)
            provider.save()
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', args=[provider.email_verification_token])
            )
            context = {
                'name': provider.name,
                'verification_url': verification_url
            }
            html_message = render_to_string('service_providers/verification_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                'Verify your email address',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message
            )
            
            # Log the registration in admin
            LogEntry.objects.log_action(
                user_id=1,  # Admin user ID
                content_type_id=ContentType.objects.get_for_model(ServiceProvider).pk,
                object_id=provider.pk,
                object_repr=str(provider),
                action_flag=ADDITION,
                change_message='Service provider registered'
            )
            
            # Authenticate and login the user
            user = authenticate(request, email=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! A verification email has been sent. You can verify your email later.')
                return redirect('provider_dashboard')
            else:
                messages.error(request, 'Error logging in after registration. Please try logging in manually.')
                return redirect('provider_login')
        else:
            print("Form errors:", form.errors)  # Debug print
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ServiceProviderRegistrationForm()
    
    # Get all service types for the form
    service_types = ServiceType.objects.all()
    return render(request, 'service_providers/signup.html', {
        'form': form,
        'service_types': service_types
    })

def verify_email(request, token):
    provider = get_object_or_404(ServiceProvider, email_verification_token=token)
    if not provider.is_verified:
        provider.is_verified = True
        provider.email_verification_token = ''  # Clear the token after verification
        provider.save()
        
        # Log the verification in admin
        LogEntry.objects.log_action(
            user_id=1,
            content_type_id=ContentType.objects.get_for_model(ServiceProvider).pk,
            object_id=provider.pk,
            object_repr=str(provider),
            action_flag=CHANGE,
            change_message='Email verified'
        )
        
        messages.success(request, 'Your email has been verified. You can now log in.')
    else:
        messages.info(request, 'Your email was already verified.')
    return redirect('login')

@provider_required
def provider_dashboard(request):
    provider = get_object_or_404(ServiceProvider, user=request.user)
    
    # Get the service type name and normalize it for matching
    service_type = provider.service_type.name.lower().strip()
    
    # Map provider's service type to allservices service type
    normalized_service_type = 'appliance' if 'appliance' in service_type else service_type.split()[0]
    print(f"[DEBUG] Provider: {provider.name}, Original Service Type: {service_type}")
    print(f"[DEBUG] Normalized Service Type: {normalized_service_type}")
    
    # Get ServiceBooking requests
    from allservices.models import ServiceBooking, SERVICE_TYPES, ServiceProvider as AllServicesProvider, SERVICE_CATEGORIES
    
    # Get or create the corresponding provider in allservices app
    try:
        allservices_provider = AllServicesProvider.objects.get(user=provider.user)
        print(f"[DEBUG] Found existing allservices provider: {allservices_provider.name}")
        
        # Update service type if needed
        if allservices_provider.service_type != normalized_service_type:
            allservices_provider.service_type = normalized_service_type
            allservices_provider.save()
            print(f"[DEBUG] Updated provider service type to: {normalized_service_type}")
            
    except AllServicesProvider.DoesNotExist:
        print(f"[DEBUG] Creating new allservices provider for: {provider.name}")
        # Create a provider in allservices if it doesn't exist
        allservices_provider = AllServicesProvider.objects.create(
            user=provider.user,
            name=provider.name,
            email=provider.user.email,
            phone=provider.phone,
            address=provider.location,
            age=provider.age,
            service_type=normalized_service_type,
            is_active=True
        )
    
    # Get all related service types that this provider can handle
    main_category = normalized_service_type
    related_services = []
    
    # First check if this service type has a category
    for category, services in SERVICE_CATEGORIES.items():
        if normalized_service_type in services:
            main_category = category
            related_services = services
            break
    
    # If no category found, add the service type itself
    if not related_services:
        related_services = [normalized_service_type]
    
    print(f"[DEBUG] Main category: {main_category}")
    print(f"[DEBUG] Related services: {related_services}")
    
    # Get all pending service requests for this service type and related services
    pending_requests = ServiceBooking.objects.select_related('user').filter(
        service__in=related_services,
        status='pending'
    ).order_by('-created_at')
    
    # Get requests that this provider has accepted
    accepted_requests = ServiceBooking.objects.select_related('user').filter(
        service__in=related_services,
        status='approved',
        provider=allservices_provider
    ).order_by('-created_at')
    
    # Get requests that this provider has completed
    completed_requests = ServiceBooking.objects.select_related('user').filter(
        service__in=related_services,
        status='completed',
        provider=allservices_provider
    ).order_by('-created_at')
    
    # Debug print
    print(f"[DEBUG] Found requests for {normalized_service_type} and related services:")
    print(f"[DEBUG] All Pending: {pending_requests.count()}")
    for req in pending_requests:
        print(f"[DEBUG] - {req.name} ({req.email}) - Service: {req.service} - Provider: {req.provider}")
    print(f"[DEBUG] Accepted: {accepted_requests.count()}")
    print(f"[DEBUG] Completed: {completed_requests.count()}")
    
    context = {
        'provider': provider,
        'pending_requests': pending_requests,
        'accepted_requests': accepted_requests,
        'completed_requests': completed_requests,
        'total_pending': pending_requests.count(),
        'total_accepted': accepted_requests.count(),
        'total_completed': completed_requests.count(),
        'service_type': provider.service_type.name.title(),
        'provider_services': [s.title() for s in related_services],
        'template_version': timezone.now().timestamp()  # Add version to force template reload
    }
    
    response = render(request, 'service_providers/dashboard.html', context)
    
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

@login_required
def pending_requests(request):
    """AJAX endpoint for real-time pending requests updates"""
    provider = get_object_or_404(ServiceProvider, user=request.user)
    
    # Convert ServiceType model instance to string service type
    service_type = provider.service_type.name.lower()
    
    # Get ServiceBooking requests
    from allservices.models import ServiceBooking
    
    # Get pending requests for this service type
    pending_requests = ServiceBooking.objects.select_related('user').filter(
        service=service_type,
        status='pending',
        provider__isnull=True
    ).order_by('-created_at')
    
    # Render only the pending requests table
    html = render_to_string('service_providers/pending_requests_table.html', {
        'pending_requests': pending_requests
    }, request=request)
    
    return JsonResponse({
        'count': pending_requests.count(),
        'html': html
    })

@provider_required
def handle_request(request, request_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    from allservices.models import ServiceBooking, ServiceProvider as AllServicesProvider, SERVICE_CATEGORIES
    
    service_request = get_object_or_404(ServiceBooking, id=request_id)
    provider = get_object_or_404(ServiceProvider, user=request.user)
    
    print(f"[DEBUG] Handling request {request_id} for provider {provider.name}")
    
    # Normalize provider's service type
    service_type = provider.service_type.name.lower().strip()
    normalized_service_type = 'appliance' if 'appliance' in service_type else service_type.split()[0]
    
    # Get or create the corresponding provider in allservices app
    try:
        allservices_provider = AllServicesProvider.objects.get(user=provider.user)
        print(f"[DEBUG] Found existing allservices provider: {allservices_provider.name}")
        
        # Update service type if needed
        if allservices_provider.service_type != normalized_service_type:
            allservices_provider.service_type = normalized_service_type
            allservices_provider.save()
    except AllServicesProvider.DoesNotExist:
        print(f"[DEBUG] Creating new allservices provider for: {provider.name}")
        allservices_provider = AllServicesProvider.objects.create(
            user=provider.user,
            name=provider.name,
            email=provider.user.email,
            phone=provider.phone,
            address=provider.location,
            age=provider.age,
            service_type=normalized_service_type,
            is_active=True
        )
    
    action = request.POST.get('action')
    print(f"[DEBUG] Action: {action}")
    print(f"[DEBUG] Request service type: {service_request.service}")
    print(f"[DEBUG] Provider service type: {normalized_service_type}")
    
    # Get related services for this provider
    related_services = []
    for category, services in SERVICE_CATEGORIES.items():
        if normalized_service_type in services:
            related_services = services
            break
    if not related_services:
        related_services = [normalized_service_type]
    
    # Verify this request is for a service type this provider can handle
    if service_request.service not in related_services:
        print(f"[DEBUG] Service type mismatch: {service_request.service} not in {related_services}")
        return JsonResponse({
            'status': 'error',
            'message': 'This request is not for your service type.'
        })
    
    if action == 'accept':
        if service_request.status != 'pending' or service_request.provider is not None:
            print(f"[DEBUG] Request already handled: status={service_request.status}, provider={service_request.provider}")
            return JsonResponse({
                'status': 'error',
                'message': 'This request has already been handled.'
            })
        service_request.status = 'approved'
        service_request.provider = allservices_provider
        service_request.save()
        print(f"[DEBUG] Request accepted: {service_request.id}")
        
        # Send email to user
        context = {
            'user_name': service_request.name,
            'provider_name': provider.name,
            'service_type': service_request.service
        }
        html_message = render_to_string('emails/request_accepted.html', context)
        send_mail(
            'Your Service Request has been Accepted',
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [service_request.email],
            html_message=html_message
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Request accepted successfully'
        })
        
    elif action == 'reject':
        if service_request.status != 'pending' or service_request.provider is not None:
            print(f"[DEBUG] Request already handled: status={service_request.status}, provider={service_request.provider}")
            return JsonResponse({
                'status': 'error',
                'message': 'This request has already been handled.'
            })
        service_request.status = 'rejected'
        service_request.save()
        print(f"[DEBUG] Request rejected: {service_request.id}")
        
        # Send email to user
        context = {
            'user_name': service_request.name,
            'provider_name': provider.name,
            'service_type': service_request.service
        }
        html_message = render_to_string('emails/request_rejected.html', context)
        send_mail(
            'Your Service Request Status',
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [service_request.email],
            html_message=html_message
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Request rejected successfully'
        })
    
    elif action == 'complete':
        print(f"[DEBUG] Attempting to complete request {request_id}")
        print(f"[DEBUG] Current status: {service_request.status}")
        print(f"[DEBUG] Current provider: {service_request.provider}")
        print(f"[DEBUG] Expected provider: {allservices_provider}")
        
        if service_request.status != 'approved':
            print(f"[DEBUG] Cannot complete request with status: {service_request.status}")
            return JsonResponse({
                'status': 'error',
                'message': f'Only approved requests can be marked as completed. Current status: {service_request.status}'
            })
            
        if not service_request.provider:
            print(f"[DEBUG] Request has no provider assigned")
            return JsonResponse({
                'status': 'error',
                'message': 'This request has no provider assigned'
            })
            
        if service_request.provider.id != allservices_provider.id:
            print(f"[DEBUG] Provider mismatch: {service_request.provider.id} != {allservices_provider.id}")
            return JsonResponse({
                'status': 'error',
                'message': 'You can only complete requests that you have accepted'
            })
            
        service_request.status = 'completed'
        service_request.save()
        print(f"[DEBUG] Request completed successfully: {service_request.id}")
        
        # Send email to user without feedback URL
        context = {
            'user_name': service_request.name,
            'provider_name': provider.name,
            'service_type': service_request.service
        }
        html_message = render_to_string('emails/request_completed.html', context)
        send_mail(
            'Your Service Request has been Completed',
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [service_request.email],
            html_message=html_message
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Request marked as completed successfully'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid action'
    })

@login_required
def edit_profile(request):
    provider = get_object_or_404(ServiceProvider, user=request.user)
    
    if request.method == 'POST':
        form = ServiceProviderProfileForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('provider_dashboard')

@login_required
def update_photo(request):
    if request.method == 'POST' and request.FILES.get('profile_photo'):
        provider = get_object_or_404(ServiceProvider, user=request.user)
        
        # Validate file size (5MB limit)
        if request.FILES['profile_photo'].size > 5 * 1024 * 1024:
            messages.error(request, 'Profile photo must be less than 5MB')
            return redirect('provider_dashboard')
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png']
        if request.FILES['profile_photo'].content_type not in allowed_types:
            messages.error(request, 'Please upload a JPEG or PNG image')
            return redirect('provider_dashboard')
        
        # Update profile photo
        provider.profile_photo = request.FILES['profile_photo']
        provider.save()
        
        messages.success(request, 'Profile photo updated successfully')
    
    return redirect('provider_dashboard')

@login_required
def resend_verification(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    provider = get_object_or_404(ServiceProvider, user=request.user)
    
    if provider.is_verified:
        return JsonResponse({'status': 'error', 'message': 'Your email is already verified'})
    
    # Generate new verification token
    provider.email_verification_token = get_random_string(64)
    provider.save()
    
    # Send verification email
    verification_url = request.build_absolute_uri(
        reverse('verify_email', args=[provider.email_verification_token])
    )
    context = {
        'name': provider.name,
        'verification_url': verification_url
    }
    html_message = render_to_string('service_providers/verification_email.html', context)
    
    try:
        send_mail(
            'Verify your email address',
            strip_tags(html_message),
            settings.DEFAULT_FROM_EMAIL,
            [provider.user.email],
            html_message=html_message
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def provider_notifications(request):
    provider = get_object_or_404(ServiceProvider, user=request.user)
    last_id = request.GET.get('last_id', 0)
    
    # Get notifications newer than last_id
    notifications = Notification.objects.filter(
        provider=provider,
        id__gt=last_id
    ).order_by('-created_at')[:10]
    
    # Check for new service requests
    has_new_requests = ServiceRequest.objects.filter(
        service_type=provider.service_type,
        status='pending',
        created_at__gt=timezone.now() - timezone.timedelta(minutes=1)
    ).exists()
    
    # Format notifications for JSON response
    notifications_data = [{
        'id': n.id,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%b %d, %Y %I:%M %p')
    } for n in notifications]
    
    # Get count of unread notifications
    unread_count = Notification.objects.filter(
        provider=provider,
        is_read=False
    ).count()
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count,
        'has_new_requests': has_new_requests
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, provider__user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@csrf_protect
def provider_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Check if user is a service provider
            try:
                provider = ServiceProvider.objects.get(user=user)
                if not provider.is_verified:
                    messages.warning(request, 'Please verify your email before logging in.')
                    return redirect('provider_login')
                login(request, user)
                return redirect('provider_dashboard')
            except ServiceProvider.DoesNotExist:
                messages.error(request, 'This account is not registered as a service provider.')
                return redirect('provider_login')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'registration/provider_login.html') 