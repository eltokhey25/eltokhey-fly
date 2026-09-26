from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('trips/', views.trips_list, name='trips'),
    path('trips/<slug:slug>/', views.trip_detail, name='trip_detail'),
    path('about/', views.about, name='about'),
    path('booking/', views.booking, name='booking'),
    path('reviews/', views.reviews_list, name='reviews'),
    path('reviews/submit/', views.review_submit, name='review_submit'),
    path('track/', views.track_booking, name='track_booking'),
    path('offline/', views.offline, name='offline'),
    path('chat/', views.chat_page, name='chat_page'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/chat/trips/', views.chat_trips_api, name='chat_trips_api'),
    path('api/chat/booking/', views.chat_booking_api, name='chat_booking_api'),
]