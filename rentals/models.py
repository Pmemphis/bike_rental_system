from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Bike(models.Model):
    """Tracks individual physical bicycles in the fleet."""
    bike_number = models.CharField(max_length=10, unique=True, help_text="e.g., BK-001")
    is_available = models.BooleanField(default=True, help_text="Is the bike currently at the station?")
    needs_maintenance = models.BooleanField(default=False, help_text="Check this to remove bike from public view")

    def __str__(self):
        status = "🔧 Maintenance" if self.needs_maintenance else ("✅ Ready" if self.is_available else "🚲 In Use")
        return f"Bike {self.bike_number} [{status}]"

class Rental(models.Model):
    """Handles the full lifecycle of a student's ride."""
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    bike = models.ForeignKey(Bike, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Identity Verification Fields
    national_id = models.CharField(max_length=20)
    registration_number = models.CharField(max_length=50)
    # The live photo captured via webcam
    student_photo = models.ImageField(upload_to='rental_photos/%Y/%m/%d/', null=True, blank=True)

    # Timing and Billing
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_time']

    def calculate_duration(self):
        """Returns duration in minutes."""
        if self.end_time:
            diff = self.end_time - self.start_time
            return max(1, int(diff.total_seconds() / 60))
        return 0

    def calculate_cost(self):
        """Calculates cost based on KES 70 per hour (pro-rated)."""
        duration_minutes = self.calculate_duration()
        # Rate: 70 / 60 per minute
        cost = (duration_minutes / 60) * 70
        return round(max(10.00, cost), 2) # Minimum charge of 10 KES

    def __str__(self):
        return f"{self.customer.username} - {self.bike.bike_number if self.bike else 'No Bike'}"

class UserProfile(models.Model):
    """Extends the User model for extra student-specific data."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    total_rides = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username