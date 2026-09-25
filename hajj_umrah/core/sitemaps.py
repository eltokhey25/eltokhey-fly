from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from .models import Trip


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    items_list = [
        'core:home',
        'core:trips',
        'core:about',
        'core:reviews',
        'core:booking',
        'core:track_booking',
    ]
    priorities = {
        'core:home': 1.0,
        'core:trips': 0.9,
        'core:about': 0.7,
        'core:reviews': 0.7,
        'core:booking': 0.8,
        'core:track_booking': 0.6,
    }

    def items(self):
        return self.items_list

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.priorities[item]

    def lastmod(self, item):
        return timezone.now().date()


class TripSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Trip.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('core:trip_detail', kwargs={'slug': obj.slug})
