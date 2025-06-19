from django.contrib import admin
from django.urls import path, include
from users import views
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static

# Custom admin site configuration
admin.site.site_header = 'GharSewa Administration'
admin.site.site_title = 'GharSewa Admin'
admin.site.index_title = 'Welcome to GharSewa Admin Portal'

# Function to redirect admin to custom dashboard
def admin_redirect(request):
    if request.user.is_staff:
        return redirect('user_dashboard')
    return redirect('admin:login')

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Original Django admin
    path('admin/', admin_redirect, name='admin_redirect'),  # Custom admin redirect
    path('accounts/', include('allauth.urls')),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'), 
    path('', include('users.urls')),
    path('dashboard/', include('dashboard.urls')), 
    path('service-providers/', include('service_providers.urls')),

    path('', lambda r: redirect('index'), name='index'),
    path('about/', lambda r: render(r, 'about.html'), name='about'),
    path('services/', lambda r: render(r, 'service.html'), name='service'),
    path('team/', lambda r: render(r, 'team.html'), name='team'),
    path('testimonial/', lambda r: render(r, 'testimonial.html'), name='testimonial'),
    path('contact/', lambda r: render(r, 'contact.html'), name='contact'),

    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)