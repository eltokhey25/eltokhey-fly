from django.contrib import admin

from .models import Booking, SiteSettings, Trip


class TripAdmin(admin.ModelAdmin):
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
    list_display = ('name', 'phone', 'trip_label', 'trip_type', 'people', 'created_at')
    search_fields = ('name', 'phone', 'trip_label', 'notes')
    readonly_fields = ('name', 'phone', 'trip_label', 'trip_type', 'people', 'notes', 'created_at')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Trip, TripAdmin)