from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields, Q
from django.conf import settings
from django.contrib.auth.models import User
from .models import Rental

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
    
    # Inventory Logic
    bikes_in_use = Rental.objects.filter(is_active=True).count()
    # Pulls from settings.py (ensure TOTAL_BIKES_AVAILABLE = 10 is there)
    total_allowed = getattr(settings, 'TOTAL_BIKES_AVAILABLE', 10)
    bikes_remaining = total_allowed - bikes_in_use
    
    # Recent ride for receipt shortcut
    last_rental = Rental.objects.filter(customer=request.user, is_active=False).order_by('-end_time').first()

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "start" and not active_rental:
            if bikes_remaining > 0:
                Rental.objects.create(
                    customer=request.user,
                    national_id=request.POST.get('national_id'),
                    uni_reg_number=request.POST.get('reg_no'),
                    start_time=timezone.now(),
                    is_active=True
                )
            else:
                messages.error(request, "Sorry, no bikes available at the moment!")

        elif action == "stop" and active_rental:
            active_rental.end_time = timezone.now()
            active_rental.is_active = False
            active_rental.calculate_cost() # Triggers math from models.py
            active_rental.save()

        return redirect('dashboard')

    return render(request, 'rentals/dashboard.html', {
        'active_rental': active_rental, 
        'last_rental': last_rental,
        'bikes_remaining': max(bikes_remaining, 0) # Ensures it doesn't show negative
    })


# --- 3. STUDENT PROFILE & HISTORY ---
@login_required
def profile(request):
    # History for this specific student
    ride_history = Rental.objects.filter(customer=request.user, is_active=False).order_by('-end_time')
    
    # Calculate lifetime total spending
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
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate top 10 riders by summing their total duration (end - start)
    top_riders = User.objects.annotate(
        total_minutes=Sum(
            ExpressionWrapper(
                F('rental__end_time') - F('rental__start_time'),
                output_field=fields.DurationField()
            ),
            filter=Q(rental__start_time__gte=start_of_month, rental__is_active=False)
        )
    ).filter(total_minutes__isnull=False).order_by('-total_minutes')[:10]

    return render(request, 'rentals/leaderboard.html', {
        'top_riders': top_riders,
        'current_month': now.strftime('%B %Y')
    })