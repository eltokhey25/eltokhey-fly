from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Trip


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return ['core:home', 'core:trips', 'core:about', 'core:booking']

    def location(self, item):
        return reverse(item)


class TripSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Trip.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('core:trip_detail', kwargs={'slug': obj.slug})