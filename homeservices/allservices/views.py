from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import ServiceBooking
from .forms import ServiceBookingForm

template_map = {
    'appliance': 'service/appliance.html',
    'cleaning': 'service/cleaning.html',
    'electrical': 'service/electrical.html',
    'flooring': 'service/flooring.html',
    'painting': 'service/painting.html',
    'plastering': 'service/plastering.html',
    'plumbing': 'service/plumbing.html',
    'roofing': 'service/roofing.html',
}

@login_required(login_url='/login/')
def service_list(request):
    return render(request, 'service/service.html')

@login_required(login_url='/login/')
def book_service(request, service_type):
    if service_type not in template_map:
        messages.error(request, "Invalid service type.")
        return redirect('service')

    if request.method == 'POST':
        form = ServiceBookingForm(request.POST, service_type=service_type)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.service = service_type  # Set the service type
            booking.status = 'pending'  # Set initial status
            booking.save()
            
            request.session['last_booking_id'] = booking.id
            messages.success(request, "Service booked successfully!")
            return redirect('booking_success')
        else:
            print("Form errors:", form.errors)  # Debugging
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceBookingForm(service_type=service_type)
    
    return render(request, template_map[service_type], {
        'form': form,
        'service_type': service_type
    })

@login_required(login_url='/login/')
def booking_success(request):
    booking_id = request.session.get('last_booking_id')
    booking = None
    
    if booking_id:
        try:
            booking = ServiceBooking.objects.get(id=booking_id, user=request.user)
            del request.session['last_booking_id']
        except ServiceBooking.DoesNotExist:
            pass
    
    return render(request, 'service/booking_success.html', {
        'booking': booking
    })