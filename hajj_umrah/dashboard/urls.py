from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('login/', views.DashboardLoginView.as_view(), name='login'),
    path('logout/', views.dashboard_logout, name='logout'),

    path('trips/', views.trip_list, name='trips'),
    path('trips/add/', views.trip_create, name='trip_add'),
    path('trips/<slug:slug>/edit/', views.trip_edit, name='trip_edit'),
    path('trips/<slug:slug>/delete/', views.trip_delete, name='trip_delete'),

    path('bookings/', views.booking_list, name='bookings'),
    path('bookings/add/', views.booking_create, name='booking_add'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),

    path('settings/', views.settings_edit, name='settings'),
    path('sections/', views.sections_view, name='sections'),

    path('media/', views.media_list, name='media'),
    path('media/upload/', views.media_upload, name='media_upload'),
    path('media/<int:pk>/delete/', views.media_delete, name='media_delete'),

    path('users/', views.user_list, name='users'),
    path('users/add/', views.user_create, name='user_add'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    path('preview/', views.preview, name='preview'),
]