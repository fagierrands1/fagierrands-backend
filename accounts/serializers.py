from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile, AssistantVerification, EmailVerification

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    account_manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                  'phone_number', 'referral_code', 'is_verified', 'email_verified', 
                  'date_joined', 'account_manager', 'account_manager_name']
        read_only_fields = ['id', 'referral_code', 'is_verified', 'email_verified', 'date_joined', 'account_manager_name']
    
    def get_account_manager_name(self, obj):
        if obj.account_manager:
            return f"{obj.account_manager.first_name} {obj.account_manager.last_name}".strip() or obj.account_manager.username
        return None
    
    def validate_account_manager(self, value):
        """Validate that account_manager is a handler"""
        if value and value.user_type != 'handler':
            raise serializers.ValidationError("Account manager must be a handler")
        return value

class AssistantDetailSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for handlers to view assistant details including verification info
    """
    verification_status = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()
    verification_details = serializers.SerializerMethodField()
    full_name_from_verification = serializers.SerializerMethodField()
    area_of_operation = serializers.SerializerMethodField()
    years_of_experience = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
            'phone_number', 'is_verified', 'email_verified', 'date_joined',
            'verification_status', 'user_role', 'service_type', 'verification_details',
            'full_name_from_verification', 'area_of_operation', 'years_of_experience'
        ]
        read_only_fields = [
            'id', 'is_verified', 'email_verified', 'date_joined',
            'verification_status', 'user_role', 'service_type', 'verification_details',
            'full_name_from_verification', 'area_of_operation', 'years_of_experience'
        ]
    
    def get_verification_status(self, obj):
        """Get the verification status of the assistant"""
        try:
            verification = obj.verification
            return verification.status
        except AssistantVerification.DoesNotExist:
            return 'not_submitted'
    
    def get_user_role(self, obj):
        """Get whether the assistant is a rider or service provider"""
        try:
            verification = obj.verification
            return verification.user_role
        except AssistantVerification.DoesNotExist:
            return None
    
    def get_service_type(self, obj):
        """Get the service type if the assistant is a service provider"""
        try:
            verification = obj.verification
            if verification.user_role == 'service_provider':
                return verification.service
            return None
        except AssistantVerification.DoesNotExist:
            return None
    
    def get_verification_details(self, obj):
        """Get additional verification details"""
        try:
            verification = obj.verification
            return {
                'submitted_at': verification.submitted_at,
                'verified_at': verification.verified_at,
                'rejected_reason': verification.rejected_reason,
                'id_number': verification.id_number,
                'driving_license_number': verification.driving_license_number if verification.user_role == 'rider' else None,
            }
        except AssistantVerification.DoesNotExist:
            return None
    
    def get_full_name_from_verification(self, obj):
        """Get the full legal name from verification"""
        try:
            verification = obj.verification
            return verification.full_name
        except AssistantVerification.DoesNotExist:
            return f"{obj.first_name} {obj.last_name}"
    
    def get_area_of_operation(self, obj):
        """Get the area of operation"""
        try:
            verification = obj.verification
            return verification.area_of_operation
        except AssistantVerification.DoesNotExist:
            return None
    
    def get_years_of_experience(self, obj):
        """Get years of experience"""
        try:
            verification = obj.verification
            return verification.years_of_experience
        except AssistantVerification.DoesNotExist:
            return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 
                 'user_type', 'phone_number', 'referral_code']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        referral_code = validated_data.pop('referral_code', None)
        
        user = User.objects.create_user(**validated_data)
        # Profile is automatically created by the post_save signal
        
        # Process referral if a code was provided
        if referral_code:
            try:
                # Find the referrer by referral_code (FAGI + up to 4 digits)
                referrer = User.objects.get(referral_code=referral_code)
                # Don't allow self-referrals
                if referrer.id != user.id:
                    # Link who referred this user
                    user.referred_by = referrer
                    user.save(update_fields=['referred_by'])
                    # Award 50 points to the new user for signing up with a referral code
                    from .models import WalletTransaction
                    user.profile.wallet_points += 50
                    user.profile.save(update_fields=['wallet_points'])
                    WalletTransaction.objects.create(
                        user=user,
                        points=50,
                        amount_equivalent=50,
                        transaction_type='earn',
                        reference='signup_referral'
                    )
            except User.DoesNotExist:
                # Invalid referral code - ignore silently
                pass
        
        return user

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'profile_picture_url', 'bio', 'address']

# AssistantVerification serializers (imports already done above)

class AssistantVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantVerification
        fields = [
            'id', 'user', 'user_role', 'full_name', 'id_number', 
            'phone_number', 'area_of_operation', 'years_of_experience',
            'id_front_url', 'id_back_url', 'selfie_url',
            'driving_license_number', 'driving_license_url',
            'service', 'certificate_url', 'status',
            'submitted_at', 'verified_at', 'rejected_reason',
            'less_than_a_year_experience'
        ]
        read_only_fields = ['status', 'submitted_at', 'verified_at', 'rejected_reason']
    
    def validate(self, data):
        """
        Custom validation for role-specific fields
        """
        user_role = data.get('user_role')
        
        if user_role == 'rider':
            if not data.get('driving_license_number'):
                raise serializers.ValidationError("Driving license number is required for riders")
            if not data.get('driving_license_url'):
                raise serializers.ValidationError("Driving license image is required for riders")
        
        elif user_role == 'service_provider':
            if not data.get('service'):
                raise serializers.ValidationError("Service type is required for service providers")
            if not data.get('certificate_url'):
                raise serializers.ValidationError("Certificate image is required for service providers")
        
        # Required for all roles
        required_fields = ['id_front_url', 'id_back_url', 'selfie_url']
        for field in required_fields:
            if not data.get(field):
                field_name = field.replace('_url', '').replace('_', ' ').title()
                raise serializers.ValidationError(f"{field_name} is required")
        
        return data

class VerificationStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for admins/handlers to update verification status
    """
    class Meta:
        model = AssistantVerification
        fields = ['id', 'status', 'rejected_reason']
    
    def validate_status(self, value):
        """Validate status transitions"""
        if value not in ['pending', 'verified', 'rejected']:
            raise serializers.ValidationError("Invalid status value")
        
        # If rejecting, ensure reason is provided
        if value == 'rejected' and not self.initial_data.get('rejected_reason'):
            raise serializers.ValidationError("Rejection reason must be provided")
        
        return value

class VerificationStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for users to check their verification status
    """
    class Meta:
        model = AssistantVerification
        fields = ['id', 'status', 'submitted_at', 'verified_at', 'rejected_reason']
        read_only_fields = ['id', 'status', 'submitted_at', 'verified_at', 'rejected_reason']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class EmailVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer for email verification tokens
    """
    class Meta:
        model = EmailVerification
        fields = ['token', 'created_at', 'expires_at', 'is_used']
        read_only_fields = ['token', 'created_at', 'expires_at', 'is_used']


class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending email verification
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that the email exists and is not already verified"""
        try:
            user = User.objects.get(email=value)
            if user.email_verified:
                raise serializers.ValidationError("This email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")


class ForgotPasswordSerializer(serializers.Serializer):
    """Request a password reset OTP"""
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    """Reset password using email + OTP"""
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs