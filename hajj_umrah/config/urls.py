"""
URL configuration for the Hajj & Umrah site.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as media_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
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