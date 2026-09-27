"""
core/urls.py
Public (visitor-facing) URL map for the site.

Mounted at the project root by config/urls.py, so every path here is prefixed
with '/' unless it carries its own leading slash. Route names are namespaced
with app_name = 'core' and are always reversed by name ({% url 'core:home' %})
so a path change never breaks a template.
"""
from django.urls import path

from . import views

# Namespace applied to every route below: 'core:home', 'core:trip_detail', ...
app_name = 'core'

urlpatterns = [
    # ---- Pages ----------------------------------------------------------
    path('', views.home, name='home'),                                # Homepage — hero, featured trips, latest reviews
    path('trips/', views.trips_list, name='trips'),                   # Full list of active trips, with filters
    path('trips/<slug:slug>/', views.trip_detail, name='trip_detail'),  # One trip: dates, price, gallery, booking CTA
    path('about/', views.about, name='about'),                       # Company / about page
    path('booking/', views.booking, name='booking'),                 # Public booking request form (POST creates a Booking)
    path('reviews/', views.reviews_list, name='reviews'),             # Paginated list of approved reviews
    path('reviews/submit/', views.review_submit, name='review_submit'),  # Review form; honeypot + IP rate limit
    path('track/', views.track_booking, name='track_booking'),        # Track a booking by reference code or phone
    path('offline/', views.offline, name='offline'),                  # PWA offline fallback page
    path('chat/', views.chat_page, name='chat_page'),                 # Full-screen chat page for mobile

    # ---- Service worker -------------------------------------------------
    # Served by a view (not staticfiles) so the served file always carries
    # no-cache headers and the worker can update itself in the wild.
    path('sw.js', views.service_worker, name='service_worker'),

    # ---- JSON API consumed by static/js/chatbot.js ---------------------
    path('api/chat/', views.chat_api, name='chat_api'),               # POST a message, get the AI reply
    path('api/chat/trips/', views.chat_trips_api, name='chat_trips_api'),     # GET the trip cards shown in chat
    path('api/chat/booking/', views.chat_booking_api, name='chat_booking_api'),  # POST a booking from inside chat
]
