"""
URL configuration for the Hajj & Umrah site.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.urls import include, path, re_path
from django.views.static import serve as media_serve

from core.sitemaps import StaticViewSitemap, TripSitemap
from core.views import robots_txt

sitemaps = {
    'static': StaticViewSitemap,
    'trips': TripSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('robots.txt', robots_txt),
    path(
        'sitemap.xml',
        sitemap_view,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path('', include('core.urls')),
]

handler404 = 'core.views.not_found'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
else:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            media_serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]