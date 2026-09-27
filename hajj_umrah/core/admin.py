"""
core/admin.py
Django admin registrations. The custom dashboard in dashboard/ is the
day-to-day tool; this module stays as a fast data-surgery fallback.
"""
from django.contrib import admin

from .models import Booking, Review, SiteSettings, Trip


class TripAdmin(admin.ModelAdmin):
    """Trip list/change screens: pricing, dates and capacity at a glance."""

    list_display = ('name', 'trip_type', 'price', 'departure', 'return_date', 'duration', 'remaining', 'is_active')
    list_filter = ('trip_type', 'is_active')
    search_fields = ('name',)
    ordering = ('departure',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'trip_type', 'description', 'is_active')}),
        ('الحجز والسعر', {'fields': ('price', 'duration', 'departure', 'return_date', 'transport', 'capacity', 'remaining')}),
        ('برنامج السير', {'fields': ('itinerary',)}),
        ('يشمل / لا يشمل', {'fields': ('includes', 'excludes')}),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Booking queue with inline status changes.

    Everything the customer submitted is read-only here: the record is the
    audit trail, so only `status` may be edited from this screen.
    """

    list_display = ('reference_code', 'status', 'name', 'phone', 'trip_label', 'people', 'created_at')
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('name', 'phone', 'email', 'reference_code', 'trip_label', 'notes')
    readonly_fields = ('name', 'phone', 'email', 'trip_label', 'trip_type', 'people', 'notes', 'created_at', 'confirmed_at', 'handled_by')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Review moderation list, filterable by status, rating and country."""

    list_display = ('name', 'country', 'rating', 'status', 'trip', 'created_at')
    list_filter = ('status', 'rating', 'country')
    search_fields = ('name', 'country', 'text', 'trip__name')
    list_editable = ('status',)
    ordering = ('-created_at',)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Keeps SiteSettings a true singleton.

    Adding is only allowed while no row exists, and deleting is never
    allowed — templates call SiteSettings.load(), which expects pk=1.
    """

    def has_add_permission(self, request):
        """Allow adding only while the table is empty.

        Args:
            request (HttpRequest): The admin request.

        Returns:
            bool: True only when no settings row has been created yet.
        """
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Refuse deletion so the singleton row can never disappear.

        Args:
            request (HttpRequest): The admin request.
            obj (SiteSettings): The row being deleted (unused).

        Returns:
            bool: Always False.
        """
        return False


# Trip is registered last (rather than with the @admin.register decorator used
# above) only to keep the explicit ModelAdmin class visible in one place.
admin.site.register(Trip, TripAdmin)