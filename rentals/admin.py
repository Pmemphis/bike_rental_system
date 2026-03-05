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

    @admin.display(description="Status")
    def current_status_badge(self, obj):
        # Added the second argument "" to satisfy Python 3.14 requirements
        if obj.needs_maintenance:
            return format_html('<span style="color: #d9534f; font-weight: bold;">🔧 REPAIR</span>', "")
        if not obj.is_available:
            return format_html('<span style="color: #f0ad4e; font-weight: bold;">🚲 IN USE</span>', "")
        return format_html('<span style="color: #5cb85c; font-weight: bold;">✅ READY</span>', "")

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """Monitor active rides and student identity verification."""
    # Ensure these field names match your Rental model exactly
    list_display = ('id_photo_thumbnail', 'user', 'reg_number', 'bike', 'start_time', 'is_active', 'total_cost')
    list_filter = ('is_active', 'start_time')
    search_fields = ('user__username', 'reg_number', 'national_id')
    readonly_fields = ('start_time', 'end_time', 'total_cost', 'id_photo_large')
    
    fieldsets = (
        ('Student Identity', {
            'fields': ('user', 'national_id', 'reg_number', 'id_photo_large')
        }),
        ('Ride Details', {
            'fields': ('bike', 'start_time', 'end_time', 'is_active')
        }),
        ('Billing', {
            'fields': ('total_cost',)
        }),
    )

    @admin.display(description="Identity")
    def id_photo_thumbnail(self, obj):
        """Displays a small photo in the list view."""
        if obj.verification_photo:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 5px; object-fit: cover;" />', 
                obj.verification_photo.url
            )
        return "No Photo"

    @admin.display(description="Captured Verification Photo")
    def id_photo_large(self, obj):
        """Displays a large photo in the detail view."""
        if obj.verification_photo:
            return format_html(
                '<img src="{}" style="max-width: 300px; border-radius: 10px;" />', 
                obj.verification_photo.url
            )
        return "No Photo Uploaded"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'total_rides')
    search_fields = ('user__username', 'phone_number')