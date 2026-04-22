from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import random
import string


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('handler', 'Handler'),
        ('admin', 'Admin'),
        ('vendor', 'Vendor'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    
    # Phone verification fields
    phone_verified = models.BooleanField(default=False)
    phone_otp = models.CharField(max_length=4, null=True, blank=True)
    phone_otp_created_at = models.DateTimeField(null=True, blank=True)
    
    # Assistant availability
    is_online = models.BooleanField(default=False, help_text='Whether the assistant is currently online and available')
    # Referral system
    referral_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    # Account manager (handler assigned to client)
    account_manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, 
                                        related_name='managed_clients', 
                                        limit_choices_to={'user_type': 'handler'},
                                        help_text='Handler assigned as account manager for this client')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        # Ensure email uniqueness at database level
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_user_email'),
            models.UniqueConstraint(
                fields=['phone_number'], 
                condition=models.Q(phone_number__isnull=False) & ~models.Q(phone_number=''),
                name='unique_phone_number'
            )
        ]
    
    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    # Wallet fields
    wallet_points = models.PositiveIntegerField(default=0)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Rider specific fields
    plate_number = models.CharField(max_length=20, blank=True, null=True, help_text='Vehicle plate number for riders')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('earn', 'Earned Points'),
        ('redeem', 'Redeemed Points'),
        ('adjust', 'Adjustment'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    points = models.IntegerField()  # positive for earn, negative for redeem
    amount_equivalent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.points} for {self.user.username}"

class AssistantVerification(models.Model):
    """
    Model to store assistant verification details with Supabase image URLs
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    USER_ROLE_CHOICES = (
        ('rider', 'Rider'),
        ('service_provider', 'Service Provider'),
    )

    EXPERIENCE_CHOICES = (
        ('less_than_a_year', 'Less than a year'),
        ('a_year', 'A year'),
        ('more_than_a_year', '1+ years'),
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='verification',
        help_text=_("The user requesting verification")
    )
    user_role = models.CharField(
        max_length=20,
        choices=USER_ROLE_CHOICES,
        null=True,
        help_text=_("Role of the user: rider or service provider")
    )
    full_name = models.CharField(
        max_length=255,
        help_text=_("Full legal name of the assistant")
    )
    id_number = models.CharField(
        max_length=50,
        help_text=_("Government-issued ID number")
    )
    address = models.TextField(
        null=True,
        help_text=_("Current residential address")
    )
    phone_number = models.CharField(
        max_length=13,
        null=True,
        help_text=_("Contact phone number")
    )
    area_of_operation = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Area where services will be provided")
    )
    
    # Document URLs
    id_front_url = models.URLField(
        null=True, 
        blank=True,
        help_text=_("URL to ID front image in Supabase")
    )
    id_back_url = models.URLField(
        null=True, 
        blank=True,
        help_text=_("URL to ID back image in Supabase")
    )
    selfie_url = models.URLField(
        null=True, 
        blank=True,
        help_text=_("URL to selfie image in Supabase")
    )
    
    # Rider specific fields
    driving_license_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Driving license number for riders")
    )
    driving_license_url = models.URLField(
        null=True, 
        blank=True,
        help_text=_("URL to driving license image in Supabase")
    )
    
    # Service provider specific fields
    service = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Service provided by service providers")
    )
    certificate_url = models.URLField(
        null=True, 
        blank=True,
        help_text=_("URL to certificate image in Supabase")
    )
    
    years_of_experience = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        help_text=_("Years of experience"),
        default='less_than_a_year'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text=_("Current verification status")
    )
    submitted_at = models.DateTimeField(
        default=timezone.now,
        help_text=_("When the verification was submitted")
    )
    verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When the verification was approved")
    )
    rejected_reason = models.TextField(
        null=True, 
        blank=True,
        help_text=_("Reason for rejection if applicable")
    )
    
    # Flag to indicate less than a year experience for separate storage
    less_than_a_year_experience = models.BooleanField(
        default=False,
        help_text=_("Flag for users with less than a year of experience")
    )
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = _("Assistant Verification")
        verbose_name_plural = _("Assistant Verifications")
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"


class EmailVerification(models.Model):
    """
    Model to handle email verification tokens
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Email Verification")
        verbose_name_plural = _("Email Verifications")
    
    def __str__(self):
        return f"Email verification for {self.user.email}"
    
    def is_expired(self):
        """Check if the verification token has expired"""
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 24 hours from creation
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)


class EmailOTP(models.Model):
    """
    Model to handle SMTP-based OTP codes (6-digit numeric codes)
    Separate from EmailVerification to avoid UUID conflicts
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    otp_code = models.CharField(max_length=6, db_index=True)  # 6-digit OTP
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Email OTP")
        verbose_name_plural = _("Email OTPs")
        # Allow multiple unused OTPs per user (in case they request multiple)
        unique_together = []
    
    def __str__(self):
        return f"OTP {self.otp_code} for {self.user.email}"
    
    def is_expired(self):
        """Check if OTP is expired (1 hour)"""
        from datetime import timedelta
        return timezone.now() - self.created_at > timedelta(hours=1)
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP code"""
        return str(random.randint(100000, 999999))


class OTPVerification(models.Model):
    """
    Model to handle OTP-based email verification
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    otp_code = models.CharField(max_length=6, help_text=_("6-digit OTP code"))
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0, help_text=_("Number of verification attempts"))
    max_attempts = models.IntegerField(default=5, help_text=_("Maximum allowed attempts"))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("OTP Verification")
        verbose_name_plural = _("OTP Verifications")
    
    def __str__(self):
        return f"OTP verification for {self.user.email} - {self.otp_code}"
    
    def is_expired(self):
        """Check if the OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_max_attempts_reached(self):
        """Check if maximum attempts have been reached"""
        return self.attempts >= self.max_attempts
    
    def increment_attempts(self):
        """Increment the number of attempts"""
        self.attempts += 1
        self.save()
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            # Set expiration to 10 minutes from creation
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)