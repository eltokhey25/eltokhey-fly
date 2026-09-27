"""
config/urls.py
Root URL configuration — the single place where the project's apps are wired
to paths. Order matters: the more specific prefixes (admin, dashboard) are
declared before the catch-all public site mounted at ''.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve as media_serve

from core.sitemaps import StaticViewSitemap, TripSitemap
from core.views import robots_txt

# Sitemap sections merged by django.contrib.sitemaps into /sitemap.xml.
# Key = section name in the URL, value = the Sitemap class.
sitemaps = {
    'static': StaticViewSitemap,   # Fixed public pages (home, trips, about…)
    'trips': TripSitemap,          # One entry per active trip
}

urlpatterns = [
    # Django's built-in admin, still available for quick data surgery.
    path('admin/', admin.site.urls),

    # Custom staff dashboard (trips, bookings, reviews, media, users).
    path('dashboard/', include('dashboard.urls')),

    # ---- SEO endpoints --------------------------------------------------
    path('robots.txt', robots_txt),                                   # Allow everything, advertise the sitemap
    path(
        'sitemap.xml',
        sitemap_view,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),

    # Google Search Console HTML-file verification.
    path(
        'google949f04ecbcd2e64b.html',
        TemplateView.as_view(
            template_name='google949f04ecbcd2e64b.html',
            content_type='text/html'
        ),
        name='google_verification',
    ),

    # Public site last: mounted at the root, so it must not shadow the above.
    path('', include('core.urls')),
]

# ---- Error handlers ----------------------------------------------------
# Rendered by Django for any 404 / 403 raised inside the project.
handler404 = 'core.views.not_found'                 # Branded 404 page
handler403 = 'dashboard.views.permission_denied'    # Branded 403 page

# ---- Media / static serving -------------------------------------------
# In DEBUG the dev server serves both from the source folders.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
else:
    # In production web.py/Nginx/gunicorn serves /static/ directly; user
    # uploads under media/ still need Django because they live outside it.
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            media_serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
