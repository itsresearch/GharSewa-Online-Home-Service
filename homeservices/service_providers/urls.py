from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.provider_login, name='provider_login'),
    path('signup/', views.provider_signup, name='provider_signup'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('pending-requests/', views.pending_requests, name='pending_requests'),
    path('handle-request/<int:request_id>/', views.handle_request, name='handle_request'),
    path('provider-profile/edit/', views.edit_profile, name='provider_edit_profile'),
    path('update-photo/', views.update_photo, name='update_photo'),
    path('notifications/', views.provider_notifications, name='provider_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
] 