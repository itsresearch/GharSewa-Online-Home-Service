from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ServiceRequestForm
from service_providers.models import ServiceRequest, Notification
from .models import Service

def service_list(request):
    services = Service.objects.all()
    return render(request, 'service_list.html', {'services': services})

@login_required
def request_service(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.user = request.user
            service_request.save()
            
            # Create notifications for service providers
            Notification.create_service_request_notification(service_request)
            
            messages.success(request, 'Your service request has been submitted successfully!')
            return redirect('dashboard')
    else:
        form = ServiceRequestForm()
    
    return render(request, 'services/request_service.html', {
        'form': form
    })

