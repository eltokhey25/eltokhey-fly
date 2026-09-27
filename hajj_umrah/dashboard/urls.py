"""
dashboard/urls.py
URL map for the staff-facing admin dashboard.

Mounted under '/dashboard/' by config/urls.py. Every view is protected by a
role check in dashboard/permissions.py (staff_required / superuser_required),
so adding a route here does not by itself expose anything — but keep the
decorator in mind when adding new entries.
"""
from django.urls import path

from . import views

# Namespace applied to every route below: 'dashboard:overview', etc.
app_name = 'dashboard'

urlpatterns = [
    # ---- Shell ----------------------------------------------------------
    path('', views.overview, name='overview'),                                  # Dashboard home: counters + recent activity
    path('login/', views.DashboardLoginView.as_view(), name='login'),           # Staff login (redirects authenticated users to overview)
    path('logout/', views.dashboard_logout, name='logout'),                     # POST-only logout
    path('sw.js', views.service_worker, name='service_worker'),                 # Dashboard-scoped service worker
    path('offline/', views.offline, name='offline'),                            # Offline fallback for the dashboard PWA

    # ---- Trips ----------------------------------------------------------
    path('trips/', views.trip_list, name='trips'),                              # List with active/hidden filters
    path('trips/add/', views.trip_create, name='trip_add'),                     # Create a trip
    path('trips/<int:pk>/move-up/', views.trip_move_up, name='trip_move_up'),   # Reorder: swap with the trip above
    path('trips/<int:pk>/move-down/', views.trip_move_down, name='trip_move_down'),  # Reorder: swap with the trip below
    path('trips/<slug:slug>/edit/', views.trip_edit, name='trip_edit'),         # Edit a trip (keyed by slug, as in the public URL)
    path('trips/<slug:slug>/delete/', views.trip_delete, name='trip_delete'),   # POST-only delete

    # ---- Bookings -------------------------------------------------------
    path('bookings/', views.booking_list, name='bookings'),                      # List with per-status filters
    path('bookings/add/', views.booking_create, name='booking_add'),             # Create a booking by hand (walk-ins)
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),    # Full booking record + contact actions
    path('bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),      # POST-only delete
    path('bookings/<int:pk>/confirm/', views.booking_confirm, name='booking_confirm'),  # Pending -> confirmed (sends WhatsApp + email)
    path('bookings/<int:pk>/reject/', views.booking_reject, name='booking_reject'),     # Pending -> rejected (sends WhatsApp)
    path('bookings/<int:pk>/complete/', views.booking_complete, name='booking_complete'),  # Confirmed -> completed

    # ---- Reviews --------------------------------------------------------
    path('reviews/', views.review_list, name='reviews'),                         # Moderation queue
    path('reviews/<int:pk>/', views.review_detail, name='review_detail'),       # Single review
    path('reviews/<int:pk>/approve/', views.review_approve, name='review_approve'),  # Publish to the public site
    path('reviews/<int:pk>/reject/', views.review_reject, name='review_reject'),     # Keep unpublished, store the reason
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),      # POST-only delete

    # ---- Site content ---------------------------------------------------
    path('settings/', views.settings_edit, name='settings'),                     # SiteSettings singleton (company, phone, social)
    path('sections/', views.sections_view, name='sections'),                     # Home-page section ordering / visibility

    # ---- Media library --------------------------------------------------
    path('media/', views.media_list, name='media'),                              # List uploaded images
    path('media/upload/', views.media_upload, name='media_upload'),              # Upload an image
    path('media/<int:pk>/delete/', views.media_delete, name='media_delete'),     # POST-only delete

    # ---- Users (superusers only) ----------------------------------------
    path('users/', views.user_list, name='users'),                               # List staff accounts
    path('users/add/', views.user_create, name='user_add'),                      # Create a staff account
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),             # Change role / reset password
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),       # POST-only delete (self-delete blocked)

    # ---- Misc -----------------------------------------------------------
    path('preview/', views.preview, name='preview'),                             # Full-page preview of the public site
]
