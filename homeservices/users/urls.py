from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.contrib import admin

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.select_signup_type, name='signup'),
    path('signup/user/', views.user_signup, name='user_signup'),
    path('signup/provider/', views.provider_signup, name='provider_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('appointment/', views.appointment, name='appointment'),
    path('contact/', views.contact_view, name='contact'),
    path('feature/', views.feature, name='feature'),
    path('service/', views.service, name='service'),
    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('painting/', views.painting, name='painting'),
    path('plastering/', views.plastering, name='plastering'),
    path('electrical/', views.electrical, name='electrical'),
    path('plumbing/', views.plumbing, name='plumbing'),
    path('carpentry/', views.carpentry, name='carpentry'),
    path('flooring/', views.flooring, name='flooring'),
    path('roofing/', views.roofing, name='roofing'),
    path('cleaning/', views.cleaning, name='cleaning'),
    path('appliance/', views.appliance, name='appliance'),
    path('services/', include('allservices.urls')),
    path('user/home/', views.user_home, name='user_home'),
    path('user/book-service/', views.book_service, name='book_service'),
    
    # Profile Management URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('service-requests/', views.service_requests, name='service_requests'),
    path('service-requests/<int:request_id>/', views.view_request, name='view_request'),
    path('cancel-request/<int:request_id>/', views.cancel_request, name='cancel_request'),
]
