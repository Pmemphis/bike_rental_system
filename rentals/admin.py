import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import Rental

# 1. CUSTOM ACTION: EXPORT TO EXCEL (CSV)
@admin.action(description='Export Selected to CSV (Excel)')
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bike_rentals_report.csv"'
    
    writer = csv.writer(response)
    # Header Row
    writer.writerow(['Customer', 'National ID', 'Uni Reg No', 'Start Time', 'End Time', 'Total Cost', 'Paid Status'])
    
    # Data Rows
    for obj in queryset:
        writer.writerow([
            obj.customer.username, 
            obj.national_id, 
            obj.uni_reg_number, 
            obj.start_time.strftime('%Y-%m-%d %H:%M') if obj.start_time else "N/A", 
            obj.end_time.strftime('%Y-%m-%d %H:%M') if obj.end_time else "N/A", 
            obj.total_cost, 
            "Paid" if obj.is_paid else "Pending"
        ])
    return response

# 2. CUSTOM ACTION: MARK AS PAID
@admin.action(description='Mark selected rides as PAID')
def make_paid(modeladmin, request, queryset):
    queryset.update(is_paid=True)

# 3. ADMIN DASHBOARD CONFIGURATION
@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    # What columns you see in the list view
    list_display = ('customer', 'uni_reg_number', 'national_id', 'start_time', 'total_cost', 'is_active', 'is_paid')
    
    # Sidebar filters for quick sorting
    list_filter = ('is_active', 'is_paid', 'start_time')
    
    # Search bar (Search by ID or Reg Number)
    search_fields = ('national_id', 'uni_reg_number', 'customer__username')
    
    # Add our custom buttons to the "Actions" dropdown
    actions = [make_paid, export_to_csv]
    
    # Make timestamps read-only so Admin doesn't accidentally change them
    readonly_fields = ('start_time', 'end_time', 'total_cost')

    # Organize the detail view when you click on a specific rental
    fieldsets = (
        ('Customer Info', {
            'fields': ('customer', 'national_id', 'uni_reg_number')
        }),
        ('Timing & Billing', {
            'fields': ('start_time', 'end_time', 'total_cost', 'is_active', 'is_paid')
        }),
    )