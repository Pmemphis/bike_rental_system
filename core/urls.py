from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
# Added leaderboard to the import list below
from rentals.views import dashboard, register, receipt, profile, leaderboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='rentals/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    
    # Features
    path('receipt/<int:rental_id>/', receipt, name='receipt'),
    path('profile/', profile, name='profile'),
    path('leaderboard/', leaderboard, name='leaderboard'), # Fixed: removed 'views.' prefix

    # Password Reset Flow
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='rentals/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='rentals/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='rentals/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='rentals/password_reset_complete.html'),
         name='password_reset_complete'),
]