from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('trips/', views.trips_list, name='trips'),
    path('trips/<slug:slug>/', views.trip_detail, name='trip_detail'),
    path('about/', views.about, name='about'),
    path('booking/', views.booking, name='booking'),
]