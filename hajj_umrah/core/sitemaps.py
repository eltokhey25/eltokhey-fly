"""
core/sitemaps.py
SEO sitemaps: one for the fixed public pages, one for the trip detail pages.
Wired up in: config/urls.py -> sitemap_view({'sitemaps': ...}).
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from .models import Trip


class StaticViewSitemap(Sitemap):
    """Sitemap for the fixed, always-present public pages.

    Pages are listed by URL name rather than path so a route rename in
    core/urls.py cannot silently break the sitemap.
    """

    changefreq = 'weekly'
    priority = 0.5

    # URL names of the pages included in the sitemap.
    items_list = [
        'core:home',
        'core:trips',
        'core:about',
        'core:reviews',
        'core:booking',
        'core:track_booking',
    ]
    # Hand-tuned priorities; the homepage outranks the utility pages.
    priorities = {
        'core:home': 1.0,
        'core:trips': 0.9,
        'core:about': 0.7,
        'core:reviews': 0.7,
        'core:booking': 0.8,
        'core:track_booking': 0.6,
    }

    def items(self):
        """Return the URL names to publish.

        Returns:
            list[str]: Entries of `items_list`.
        """
        return self.items_list

    def location(self, item):
        """Resolve one URL name to its absolute path.

        Args:
            item (str): A URL name such as 'core:home'.

        Returns:
            str: The reversed path, e.g. '/about/'.
        """
        return reverse(item)

    def priority(self, item):
        """Return the hand-tuned priority for a page.

        Args:
            item (str): A URL name present in `priorities`.

        Returns:
            float: Priority between 0.0 and 1.0.
        """
        return self.priorities[item]

    def lastmod(self, item):
        """Return the modification date advertised for a static page.

        Args:
            item (str): A URL name (unused — these pages have no row to read).

        Returns:
            date: Today; static pages change whenever the site is redeployed.
        """
        return timezone.now().date()


class TripSitemap(Sitemap):
    """Sitemap of every publicly visible trip detail page."""

    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        """Return the trips to publish.

        Returns:
            QuerySet: Active trips only — hidden trips must stay out of search
                      results even if their URL is known.
        """
        return Trip.objects.filter(is_active=True)

    def lastmod(self, obj):
        """Return the trip's last edit timestamp.

        Args:
            obj (Trip): The trip being published.

        Returns:
            datetime: Value of Trip.updated_at.
        """
        return obj.updated_at

    def location(self, obj):
        """Return the trip detail path.

        Args:
            obj (Trip): The trip being published.

        Returns:
            str: e.g. '/trips/umrah-2026/'.
        """
        return reverse('core:trip_detail', kwargs={'slug': obj.slug})
