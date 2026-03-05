import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields, Q, Count
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from .models import Rental, Bike, UserProfile

# --- 1. REGISTRATION & SECURITY ---
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        t_and_c = request.POST.get('terms_accepted') # Checkbox from HTML
        
        if form.is_valid():
            if not t_and_c:
                messages.error(request, "You must agree to the Terms and Conditions to register.")
            else:
                user = form.save()
                # Create the UserProfile automatically upon registration
                UserProfile.objects.get_or_create(user=user)
                login(request, user)
                return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'rentals/register.html', {'form': form})


# --- 2. MAIN DASHBOARD (Start/Stop Ride) ---
@login_required
def dashboard(request):
    # Get current user's active ride
    active_rental = Rental.objects.filter(customer=request.user, is_active=True).first()
    
    # Inventory Logic from the Bike Model
    available_bikes = Bike.objects.filter(is_available=True, needs_maintenance=False)
    bikes_remaining = available_bikes.count()
    
    # Recent ride for receipt shortcut
    last_rental = Rental.objects.filter(customer=request.user, is_active=False).order_by('-end_time').first()

    if request.method == "POST":
        action = request.POST.get('action')

        # START RIDE LOGIC
        if action == "start" and not active_rental:
            if bikes_remaining > 0:
                # Capture the Live Photo string from the hidden input
                image_data = request.POST.get('captured_image')
                photo_file = None
                
                if image_data and ';base64,' in image_data:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    photo_file = ContentFile(
                        base64.b64decode(imgstr), 
                        name=f"id_{request.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    )

                # Assign the first available physical bike
                selected_bike = available_bikes.first()
                
                Rental.objects.create(
                    customer=request.user,
                    bike=selected_bike,
                    national_id=request.POST.get('national_id'),
                    registration_number=request.POST.get('reg_number'),
                    student_photo=photo_file,
                    start_time=timezone.now(),
                    is_active=True
                )
                
                # Mark bike as "In Use"
                selected_bike.is_available = False
                selected_bike.save()
                messages.success(request, f"Ride started with Bike {selected_bike.bike_number}!")
            else:
                messages.error(request, "Sorry, no bikes available at the moment!")

        # STOP RIDE LOGIC
        elif action == "stop" and active_rental:
            active_rental.end_time = timezone.now()
            active_rental.is_active = False
            # Triggers the KES 70/hr math from models.py
            active_rental.total_cost = active_rental.calculate_cost() 
            active_rental.save()
            
            # Release the bike back to the station
            if active_rental.bike:
                active_rental.bike.is_available = True
                active_rental.bike.save()
            
            # Update UserProfile stats
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.total_rides += 1
            profile.save()

            return redirect('receipt', rental_id=active_rental.id)

        return redirect('dashboard')

    return render(request, 'rentals/dashboard.html', {
        'active_rental': active_rental, 
        'last_rental': last_rental,
        'available_bikes_count': bikes_remaining
    })


# --- 3. STUDENT PROFILE & HISTORY ---
@login_required
def profile(request):
    ride_history = Rental.objects.filter(customer=request.user, is_active=False).order_by('-end_time')
    total_spent = ride_history.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    
    return render(request, 'rentals/profile.html', {
        'ride_history': ride_history,
        'total_spent': total_spent
    })


# --- 4. DIGITAL RECEIPT ---
@login_required
def receipt(request, rental_id):
    # Security: Ensure students can ONLY see their own receipts
    rental = get_object_or_404(Rental, id=rental_id, customer=request.user)
    return render(request, 'rentals/receipt.html', {'rental': rental})


# --- 5. MONTHLY LEADERBOARD ---
@login_required
def leaderboard(request):
    now = timezone.now()
    # Ranks by total time spent riding this month
    top_riders = User.objects.annotate(
        total_time=Sum(
            ExpressionWrapper(
                F('rentals__end_time') - F('rentals__start_time'),
                output_field=fields.DurationField()
            ),
            filter=Q(rentals__start_time__month=now.month, rentals__is_active=False)
        )
    ).filter(total_time__isnull=False).order_by('-total_time')[:10]

    return render(request, 'rentals/leaderboard.html', {
        'top_riders': top_riders,
        'current_month': now.strftime('%B %Y')
    })