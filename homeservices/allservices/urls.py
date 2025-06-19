# allservices/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('appliance/', views.book_service, {'service_type': 'appliance'}, name='book_appliance'),
    path('cleaning/', views.book_service, {'service_type': 'cleaning'}, name='book_cleaning'),
    path('electrical/', views.book_service, {'service_type': 'electrical'}, name='book_electrical'),
    path('flooring/', views.book_service, {'service_type': 'flooring'}, name='book_flooring'),
    path('painting/', views.book_service, {'service_type': 'painting'}, name='book_painting'),
    path('plastering/', views.book_service, {'service_type': 'plastering'}, name='book_plastering'),
    path('plumbing/', views.book_service, {'service_type': 'plumbing'}, name='book_plumbing'),
    path('roofing/', views.book_service, {'service_type': 'roofing'}, name='book_roofing'),
    
    path('booking_success/', views.booking_success, name='booking_success'), 
]