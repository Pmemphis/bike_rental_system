from django.contrib import admin
from django.utils.html import format_html
from .models import Bike, Rental, UserProfile

@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    """Manage the physical bike fleet."""
    list_display = ('bike_number', 'is_available', 'needs_maintenance', 'current_status_badge')
    list_filter = ('is_available', 'needs_maintenance')
    list_editable = ('needs_maintenance',)  # Toggle repairs directly from the list!
    search_fields = ('bike_number',)

    def current_status_badge(self, obj):
        if obj.needs_maintenance:
            return format_html('<span style="color: red; font-weight: bold;">🔧 REPAIR</span>')
        if not obj.is_available:
            return format_html('<span style="color: orange;">🚲 IN USE</span>')
        return format_html('<span style="color: green;">✅ READY</span>')
    
    current_status_badge.short_description = "Status"

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """Monitor active rides and student identity verification."""
    list_display = ('id_photo_thumbnail', 'customer', 'registration_number', 'bike', 'start_time', 'is_active', 'total_cost', 'is_paid')
    list_filter = ('is_active', 'is_paid', 'start_time')
    search_fields = ('customer__username', 'registration_number', 'national_id')
    readonly_fields = ('start_time', 'end_time', 'total_cost', 'id_photo_large')
    
    # Organize the detail view into sections
    fieldsets = (
        ('Student Identity', {
            'fields': ('customer', 'national_id', 'registration_number', 'id_photo_large')
        }),
        ('Ride Details', {
            'fields': ('bike', 'start_time', 'end_time', 'is_active')
        }),
        ('Billing', {
            'fields': ('total_cost', 'is_paid')
        }),
    )

    def id_photo_thumbnail(self, obj):
        """Displays a small photo in the list view."""
        if obj.student_photo:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 5px; object-fit: cover;" />', obj.student_photo.url)
        return "No Photo"
    
    id_photo_thumbnail.short_description = "Identity"

    def id_photo_large(self, obj):
        """Displays a large photo in the detail view."""
        if obj.student_photo:
            return format_html('<img src="{}" style="max-width: 300px; border-radius: 10px;" />', obj.student_photo.url)
        return "No Photo Uploaded"

    id_photo_large.short_description = "Captured Verification Photo"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'total_rides')
    search_fields = ('user__username', 'phone_number')