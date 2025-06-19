from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_dashboard, name='user_dashboard'),
    path('provider/', views.provider_dashboard, name='provider_dashboard'),
    path('service-request/<int:request_id>/update/', views.update_service_request, name='update_service_request'),
    path('profile/', views.profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/update-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('service-bookings/', views.service_bookings, name='service_bookings'),
    path('service-bookings/add/', views.add_booking, name='add_booking'),
    path('service-bookings/<int:booking_id>/', views.view_booking, name='view_booking'),
    path('service-bookings/<int:booking_id>/edit/', views.edit_booking, name='edit_booking'),
    path('service-bookings/<int:booking_id>/delete/', views.delete_booking, name='delete_booking'),
    path('service-providers/', views.service_providers, name='service_providers'),
    path('service-providers/add/', views.add_service_provider, name='add_service_provider'),
    path('service-providers/<int:provider_id>/edit/', views.edit_service_provider, name='edit_service_provider'),
    path('service-providers/<int:provider_id>/delete/', views.delete_service_provider, name='delete_service_provider'),
    path('logout/', views.logout_view, name='logout'),
    path('update_booking_status/', views.update_booking_status, name='update_booking_status'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('user_detail/<int:user_id>/', views.user_detail, name='user_detail'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('change_user_password/<int:user_id>/', views.change_user_password, name='change_user_password'),
]