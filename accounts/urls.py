from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .availability_views import AssistantAvailabilityView

urlpatterns = [
    # Standard authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('simple-login/', views.simple_login, name='simple_login'),  # Simple login endpoint
    path('debug/', views.debug_info, name='debug_info'),  # Debug endpoint
    path('token/', views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Password reset
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    
    # Supabase integration endpoints
    path('supabase/create-user/', views.supabase_user_creation, name='supabase_user_creation'),
    path('supabase/webhook/', views.supabase_auth_webhook, name='supabase_auth_webhook'),
    path('supabase/validate-token/', views.validate_supabase_token, name='validate_supabase_token'),
    
    # User and profile management
    path('user/', views.UserDetailView.as_view(), name='user_detail'),
    path('user/<int:pk>/', views.UserByIdView.as_view(), name='user_by_id'),
    path('profile/', views.ProfileView.as_view(), name='user_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Email verification (legacy)
    path('verify-email/<uuid:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('verify-email-otp/', views.VerifyEmailOTPView.as_view(), name='verify_email_otp'),
    path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('supabase/resend-verification/', views.SupabaseResendVerificationView.as_view(), name='supabase_resend_verification'),
    path('supabase/verify-otp/', views.supabase_verify_otp, name='supabase_verify_otp'),
    path('custom/resend-verification/', views.custom_resend_verification, name='custom_resend_verification'),
    path('check-email-verification/', views.CheckEmailVerificationView.as_view(), name='check_email_verification'),
    
    # OTP verification (new)
    path('send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    path('otp-status/', views.OTPStatusView.as_view(), name='otp_status'),
    
    # SMTP-based email verification (no domain restrictions)
    path('smtp/send-otp/', views.SMTPSendOTPView.as_view(), name='smtp_send_otp'),
    path('smtp/verify-otp/', views.SMTPVerifyOTPView.as_view(), name='smtp_verify_otp'),

    # Assistant list API endpoint for handlers/admins
    path('user/list/', views.AssistantListView.as_view(), name='assistant_list'),
    path('assistants/stats/', views.AssistantStatsView.as_view(), name='assistant_stats'),
    
    # Individual assistant dashboard stats
    path('assistant/dashboard-stats/', views.AssistantDashboardStatsView.as_view(), name='assistant_dashboard_stats'),
    
    # Assistant verification URLs
    path('assistant/verify/', 
         views.AssistantVerificationAPIView.as_view(), 
         name='assistant_verification'),
    
    path('assistant/verification-status/', 
         views.VerificationStatusView.as_view(), 
         name='verification_status'),
    
    # Admin verification management URLs
    path('admin/verifications/', 
         views.AssistantVerificationListView.as_view(), 
         name='verification_list'),
    
    path('admin/verifications/<int:pk>/', 
         views.AssistantVerificationDetailView.as_view(), 
         name='verification_detail'),
    
    path('admin/verifications/<int:pk>/update/', 
         views.AssistantVerificationUpdateView.as_view(), 
         name='verification_update'),

    # Assistant self-availability endpoint
    path('assistant/availability/', AssistantAvailabilityView.as_view(), name='assistant_availability'),
    
    # Handler clients endpoint
    path('handler/clients/', views.HandlerClientsView.as_view(), name='handler_clients'),
    
    # Account manager assignment
    path('user/<int:pk>/assign-account-manager/', views.AssignAccountManagerView.as_view(), name='assign_account_manager'),
]
