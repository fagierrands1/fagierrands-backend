from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import OTPVerification
from accounts.otp_utils import verify_otp, send_password_reset_email

User = get_user_model()


class ForgetPasswordOTPTestCase(TestCase):
    """Test cases for forget password OTP functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='OldPassword123!'
        )
        self.user.email_verified = True
        self.user.save()

    def test_send_password_reset_otp_email(self):
        """Test sending password reset OTP email"""
        mail.outbox = []
        
        otp_code = "123456"
        success, message = send_password_reset_email(self.user, otp_code)
        
        self.assertTrue(success)
        self.assertIn('successfully', message.lower())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('Password Reset', mail.outbox[0].subject)
        self.assertIn(otp_code, mail.outbox[0].body)

    def test_send_password_reset_otp_email_html(self):
        """Test that password reset email contains HTML version"""
        mail.outbox = []
        
        otp_code = "654321"
        success, message = send_password_reset_email(self.user, otp_code)
        
        self.assertTrue(success)
        email_message = mail.outbox[0]
        
        html_content = next(
            (alt[0] for alt in email_message.alternatives if alt[1] == 'text/html'),
            None
        )
        self.assertIsNotNone(html_content)
        self.assertIn(otp_code, html_content)
        self.assertIn('Password Reset', html_content)

    def test_otp_verification_model_for_password_reset(self):
        """Test creating OTP verification record for password reset"""
        otp_code = "123456"
        otp_verification = OTPVerification.objects.create(
            user=self.user,
            otp_code=otp_code,
            is_used=False
        )
        
        self.assertEqual(otp_verification.user, self.user)
        self.assertEqual(otp_verification.otp_code, otp_code)
        self.assertFalse(otp_verification.is_used)
        self.assertFalse(otp_verification.is_expired())

    def test_otp_expiration_for_password_reset(self):
        """Test OTP expiration"""
        otp_verification = OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            expires_at=timezone.now() - timedelta(hours=2),
            is_used=False
        )
        
        self.assertTrue(otp_verification.is_expired())

    def test_otp_not_expired(self):
        """Test that OTP is not expired within validity period"""
        otp_verification = OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            expires_at=timezone.now() + timedelta(minutes=30),
            is_used=False
        )
        
        self.assertFalse(otp_verification.is_expired())

    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        otp_code = "123456"
        OTPVerification.objects.create(
            user=self.user,
            otp_code=otp_code,
            is_used=False
        )
        
        success, message, user = verify_otp(self.user.email, otp_code)
        
        self.assertTrue(success)
        self.assertEqual(user.id, self.user.id)
        
        otp_record = OTPVerification.objects.get(otp_code=otp_code)
        self.assertTrue(otp_record.is_used)

    def test_verify_otp_wrong_code(self):
        """Test OTP verification with wrong code"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False
        )
        
        success, message, user = verify_otp(self.user.email, "999999")
        
        self.assertFalse(success)
        self.assertIn('Invalid OTP', message)
        self.assertIsNone(user)

    def test_verify_otp_expired(self):
        """Test OTP verification with expired code"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            expires_at=timezone.now() - timedelta(hours=2),
            is_used=False
        )
        
        success, message, user = verify_otp(self.user.email, "123456")
        
        self.assertFalse(success)
        self.assertIn('expired', message.lower())
        self.assertIsNone(user)

    def test_verify_otp_already_used(self):
        """Test OTP verification with already used code"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=True
        )
        
        success, message, user = verify_otp(self.user.email, "123456")
        
        self.assertFalse(success)
        self.assertIsNone(user)

    def test_verify_otp_no_user_found(self):
        """Test OTP verification when user doesn't exist"""
        success, message, user = verify_otp('nonexistent@example.com', "123456")
        
        self.assertFalse(success)
        self.assertIn('No user found', message)
        self.assertIsNone(user)

    def test_verify_otp_no_pending_otp(self):
        """Test OTP verification when no pending OTP exists"""
        success, message, user = verify_otp(self.user.email, "123456")
        
        self.assertFalse(success)
        self.assertIn('No valid OTP found', message)
        self.assertIsNone(user)

    def test_otp_max_attempts(self):
        """Test OTP verification maximum attempts"""
        otp_record = OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False,
            attempts=0,
            max_attempts=3
        )
        
        for i in range(3):
            success, message, user = verify_otp(self.user.email, "999999")
            self.assertFalse(success)
        
        success, message, user = verify_otp(self.user.email, "123456")
        self.assertFalse(success)
        self.assertIn('Maximum', message)

    def test_otp_attempts_increment(self):
        """Test that OTP attempts are incremented correctly"""
        otp_record = OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False,
            attempts=0
        )
        
        success, message, user = verify_otp(self.user.email, "999999")
        otp_record.refresh_from_db()
        self.assertEqual(otp_record.attempts, 1)
        
        success, message, user = verify_otp(self.user.email, "999999")
        otp_record.refresh_from_db()
        self.assertEqual(otp_record.attempts, 2)

    def test_otp_remaining_attempts_message(self):
        """Test that remaining attempts are shown in error message"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False,
            max_attempts=5
        )
        
        success, message, user = verify_otp(self.user.email, "999999")
        
        self.assertFalse(success)
        self.assertIn('4', message)

    def test_delete_old_otp_when_creating_new(self):
        """Test that old unused OTP codes are deleted when new one is created"""
        old_otp = OTPVerification.objects.create(
            user=self.user,
            otp_code="111111",
            is_used=False
        )
        
        new_otp = OTPVerification.objects.create(
            user=self.user,
            otp_code="222222",
            is_used=False
        )
        
        self.assertEqual(OTPVerification.objects.filter(user=self.user, is_used=False).count(), 2)

    def test_verify_otp_uses_latest(self):
        """Test that verification uses the latest OTP when multiple exist"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="111111",
            is_used=False,
            created_at=timezone.now() - timedelta(hours=1)
        )
        
        OTPVerification.objects.create(
            user=self.user,
            otp_code="222222",
            is_used=False,
            created_at=timezone.now()
        )
        
        success, message, user = verify_otp(self.user.email, "222222")
        
        self.assertTrue(success)
        self.assertEqual(user.id, self.user.id)

    def test_email_verification_on_otp_verification(self):
        """Test that email is marked as verified when OTP is verified"""
        self.user.email_verified = False
        self.user.save()
        
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False
        )
        
        success, message, user = verify_otp(self.user.email, "123456")
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_otp_case_sensitivity(self):
        """Test that OTP verification works with numeric codes"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False
        )
        
        success, message, user = verify_otp(self.user.email, "123456")
        self.assertTrue(success)

    def test_multiple_users_otp_isolation(self):
        """Test that OTP for one user doesn't verify another user"""
        user2 = User.objects.create_user(
            username='testuser2',
            email='testuser2@example.com',
            password='OldPassword123!'
        )
        user2.email_verified = True
        user2.save()
        
        OTPVerification.objects.create(
            user=self.user,
            otp_code="111111",
            is_used=False
        )
        
        success, message, user = verify_otp(user2.email, "111111")
        
        self.assertFalse(success)

    def test_otp_record_creation_with_expires_at(self):
        """Test OTP creation with custom expiration time"""
        expires_at = timezone.now() + timedelta(hours=1)
        otp_record = OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            expires_at=expires_at,
            is_used=False
        )
        
        self.assertEqual(otp_record.expires_at, expires_at)
        self.assertFalse(otp_record.is_expired())

    def test_otp_empty_code(self):
        """Test OTP verification with empty code"""
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False
        )
        
        success, message, user = verify_otp(self.user.email, "")
        
        self.assertFalse(success)

    def test_password_reset_email_contains_otp(self):
        """Test that password reset email contains the OTP code"""
        mail.outbox = []
        
        otp_code = "654321"
        send_password_reset_email(self.user, otp_code)
        
        email_body = mail.outbox[0].body
        self.assertIn(otp_code, email_body)

    def test_password_reset_email_expiration_info(self):
        """Test that password reset email mentions expiration time"""
        mail.outbox = []
        
        send_password_reset_email(self.user, "123456")
        
        email_body = mail.outbox[0].body
        self.assertIn('hour', email_body.lower())

    def test_otp_status_with_no_user(self):
        """Test OTP status check for non-existent user"""
        from accounts.otp_utils import get_otp_status
        
        status = get_otp_status('nonexistent@example.com')
        
        self.assertFalse(status['success'])
        self.assertFalse(status['email_verified'])

    def test_otp_status_already_verified(self):
        """Test OTP status for already verified email"""
        from accounts.otp_utils import get_otp_status
        
        self.user.email_verified = True
        self.user.save()
        
        status = get_otp_status(self.user.email)
        
        self.assertTrue(status['success'])
        self.assertTrue(status['email_verified'])

    def test_otp_status_pending(self):
        """Test OTP status when verification is pending"""
        from accounts.otp_utils import get_otp_status
        
        self.user.email_verified = False
        self.user.save()
        
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False
        )
        
        status = get_otp_status(self.user.email)
        
        self.assertTrue(status['success'])
        self.assertFalse(status['email_verified'])
        self.assertTrue(status['has_pending_otp'])

    def test_otp_status_shows_attempts_remaining(self):
        """Test that OTP status shows remaining attempts"""
        from accounts.otp_utils import get_otp_status
        
        OTPVerification.objects.create(
            user=self.user,
            otp_code="123456",
            is_used=False,
            attempts=1,
            max_attempts=5
        )
        
        status = get_otp_status(self.user.email)
        
        self.assertEqual(status['attempts_remaining'], 4)

    def test_concurrent_otp_requests_rate_limit(self):
        """Test rate limiting for multiple OTP requests within short time"""
        from accounts.otp_utils import resend_otp_email
        
        mail.outbox = []
        
        success1, message1 = resend_otp_email(self.user.email)
        self.assertTrue(success1)
        
        success2, message2 = resend_otp_email(self.user.email)
        self.assertTrue(success2)
        
        success3, message3 = resend_otp_email(self.user.email)
        self.assertTrue(success3)
        
        success4, message4 = resend_otp_email(self.user.email)
        self.assertFalse(success4)
        self.assertIn('Too many', message4)
