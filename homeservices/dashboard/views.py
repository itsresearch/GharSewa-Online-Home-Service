from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from allservices.models import ServiceBooking, ServiceProvider
from allservices.forms import AdminServiceBookingForm, ServiceProviderForm
import json
from users.models import CustomUser
from dashboard.forms import CustomUserChangeForm

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def user_dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    bookings_count = ServiceBooking.objects.filter(created_at__gte=month_start).count()
    customers_count = ServiceBooking.objects.filter(created_at__gte=year_start).values('email').distinct().count()
    pending_bookings = ServiceBooking.objects.filter(status='pending', preferred_date__gte=today).order_by('preferred_date')
    all_bookings = ServiceBooking.objects.filter(preferred_date__gte=today - timezone.timedelta(days=30)).order_by('preferred_date')
    completed_services_today = ServiceBooking.objects.filter(preferred_date=today, status='completed').count()
    providers_count = ServiceProvider.objects.filter(is_active=True).count()

    top_services = (ServiceBooking.objects
                    .filter(created_at__gte=month_start)
                    .values('service')
                    .annotate(total_requests=Count('id'))  
                    .order_by('-total_requests')[:5])

    chart_labels = [service['service'].title() for service in top_services]
    chart_data = [service['total_requests'] for service in top_services]

    context = {
        'bookings_count': bookings_count,
        'customers_count': customers_count,
        'pending_bookings': pending_bookings,
        'all_bookings': all_bookings,
        'completed_services_today': completed_services_today,
        'providers_count': providers_count,
        'top_services': top_services,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard/user_dashboard.html', context)

@require_POST
@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def update_booking_status(request):
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        new_status = data.get('status')

        booking = ServiceBooking.objects.get(id=booking_id, status='pending')
        if new_status == 'completed':
            booking.status = 'completed'
            booking.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
    except ServiceBooking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found or already processed'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def profile(request):
    return render(request, 'dashboard/user_profile.html')

@login_required(login_url='/login/')
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('index')
    return render(request, 'registration/logout.html')

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def service_bookings(request):
    bookings = ServiceBooking.objects.all().order_by('preferred_date')
    return render(request, 'dashboard/service_bookings.html', {'bookings': bookings})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def view_booking(request, booking_id):
    try:
        booking = ServiceBooking.objects.get(id=booking_id)
    except ServiceBooking.DoesNotExist:
        messages.error(request, "Booking not found.")
        return redirect('service_bookings')
    return render(request, 'dashboard/view_booking.html', {'booking': booking})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def edit_booking(request, booking_id):
    try:
        booking = ServiceBooking.objects.get(id=booking_id)
    except ServiceBooking.DoesNotExist:
        messages.error(request, "Booking not found.")
        return redirect('service_bookings')

    if request.method == 'POST':
        form = AdminServiceBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, "Booking updated successfully!")
            return redirect('service_bookings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminServiceBookingForm(instance=booking)
    return render(request, 'dashboard/edit_booking.html', {'form': form, 'booking': booking})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def delete_booking(request, booking_id):
    try:
        booking = ServiceBooking.objects.get(id=booking_id)
        booking.delete()
        messages.success(request, "Booking deleted successfully!")
    except ServiceBooking.DoesNotExist:
        messages.error(request, "Booking not found.")
    return redirect('service_bookings')

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def add_booking(request):
    if request.method == 'POST':
        form = AdminServiceBookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Booking added successfully!")
            return redirect('service_bookings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminServiceBookingForm()
    return render(request, 'dashboard/add_booking.html', {'form': form})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def service_providers(request):
    providers = ServiceProvider.objects.all().order_by('-created_at')
    return render(request, 'dashboard/service_providers.html', {'service_providers': providers})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def add_service_provider(request):
    if request.method == 'POST':
        form = ServiceProviderForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Service provider added successfully!")
            return redirect('service_providers')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceProviderForm()
    return render(request, 'dashboard/add_service_provider.html', {'form': form})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def edit_service_provider(request, provider_id):
    try:
        provider = ServiceProvider.objects.get(id=provider_id)
    except ServiceProvider.DoesNotExist:
        messages.error(request, "Service provider not found.")
        return redirect('service_providers')

    if request.method == 'POST':
        form = ServiceProviderForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Service provider updated successfully!")
            return redirect('service_providers')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceProviderForm(instance=provider)
    return render(request, 'dashboard/edit_service_provider.html', {'form': form, 'provider': provider})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def delete_service_provider(request, provider_id):
    try:
        provider = ServiceProvider.objects.get(id=provider_id)
        provider.delete()
        messages.success(request, "Service provider deleted successfully!")
    except ServiceProvider.DoesNotExist:
        messages.error(request, "Service provider not found.")
    return redirect('service_providers')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('user_profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'dashboard/change_password.html', {'form': form})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'dashboard/edit_profile.html', {'form': form})

@login_required
def update_profile_photo(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile_photo_url = request.POST.get('profile_photo_url')
            if profile_photo_url:
                user.profile_photo = profile_photo_url
                user.save()
                messages.success(request, 'Profile photo updated successfully!')
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'error': 'No profile photo URL provided.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def manage_users(request):
    users = CustomUser.objects.all()
    return render(request, 'dashboard/manage_users.html', {'users': users})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def user_detail(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User details updated successfully!')
            return redirect('manage_users')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'dashboard/user_detail.html', {'user': user, 'form': form})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def delete_user(request, user_id):
    if request.method == 'POST':
        user = CustomUser.objects.get(id=user_id)
        if user != request.user:  
            user.delete()
            messages.success(request, 'User deleted successfully!')
        else:
            messages.error(request, 'You cannot delete your own account!')
        return redirect('manage_users')
    return render(request, 'dashboard/confirm_delete_user.html', {'user_id': user_id})

@login_required(login_url='/login/')
@staff_member_required(login_url='/login/')
def change_user_password(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('manage_users')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user)
    return render(request, 'dashboard/change_user_password.html', {'form': form, 'user_id': user_id})

@login_required
def provider_dashboard(request):
    try:
        provider = get_object_or_404(ServiceProvider, user=request.user)
        
        print("=" * 50)
        print(f"Provider Email: {provider.email}")
        print(f"Provider Service Type: {provider.service_type}")
        
        all_bookings = ServiceBooking.objects.all()
        print(f"Total Bookings in System: {all_bookings.count()}")
        for booking in all_bookings:
            print(f"Booking ID: {booking.id}, Service: {booking.service}, Status: {booking.status}")
        
        service_type = provider.service_type.lower()
        print(f"Looking for bookings with service type: {service_type}")
        
        pending_requests = ServiceBooking.objects.filter(
            service__iexact=service_type, 
            status='pending'
        ).order_by('-created_at')
        
        accepted_requests = ServiceBooking.objects.filter(
            service__iexact=service_type,
            status='approved'
        ).order_by('-created_at')
        
        completed_requests = ServiceBooking.objects.filter(
            service__iexact=service_type,
            status='completed'
        ).order_by('-created_at')
        
        all_requests = ServiceBooking.objects.filter(
            service__iexact=service_type
        ).order_by('-created_at')
        
        print(f"Found Requests:")
        print(f"Pending: {pending_requests.count()}")
        print(f"Accepted: {accepted_requests.count()}")
        print(f"Completed: {completed_requests.count()}")
        print("=" * 50)
        
        context = {
            'provider': provider,
            'pending_requests': pending_requests,
            'accepted_requests': accepted_requests,
            'completed_requests': completed_requests,
            'all_requests': all_requests,
            'pending_count': pending_requests.count(),
            'accepted_count': accepted_requests.count(),
            'completed_count': completed_requests.count(),
            'service_type': provider.get_service_type_display()
        }
        
        return render(request, 'dashboard/provider_dashboard.html', context)
        
    except ServiceProvider.DoesNotExist:
        messages.error(request, "Service provider profile not found. Please contact admin to set up your provider profile.")
        return redirect('index')
    except Exception as e:
        print(f"Error in provider_dashboard: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('index')

@login_required
@require_POST
def update_service_request(request, request_id):
    try:
        service_request = get_object_or_404(ServiceBooking, id=request_id)
        provider = get_object_or_404(ServiceProvider, user=request.user)
        
        if service_request.service != provider.service_type:
            return JsonResponse({
                'success': False,
                'message': 'This service request is not for your service type.'
            })
        
        action = request.POST.get('action')
        if action == 'approve':
            service_request.status = 'approved'
            message = 'Service request approved successfully.'
        elif action == 'complete':
            service_request.status = 'completed'
            message = 'Service request marked as completed.'
        elif action == 'reject':
            service_request.status = 'rejected'
            message = 'Service request rejected.'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action.'
            })
        
        service_request.save()
        
        print(f"Updated request {request_id} to status: {service_request.status}")
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except ServiceBooking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Service request not found.'
        })
    except ServiceProvider.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Service provider profile not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })