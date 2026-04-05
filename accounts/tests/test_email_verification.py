from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
import uuid

from accounts.models import EmailVerification
from accounts.email_utils import send_verification_email, verify_email_token

User = get_user_model()


class EmailVerificationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_email_verification_model_creation(self):
        """Test EmailVerification model creation"""
        verification = EmailVerification.objects.create(user=self.user)
        
        self.assertIsNotNone(verification.token)
        self.assertIsNotNone(verification.expires_at)
        self.assertFalse(verification.is_used)
        self.assertFalse(verification.is_expired())

    def test_email_verification_expiration(self):
        """Test email verification expiration"""
        verification = EmailVerification.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        self.assertTrue(verification.is_expired())

    def test_send_verification_email(self):
        """Test sending verification email"""
        # Clear any existing mail
        mail.outbox = []
        
        success = send_verification_email(self.user)
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('Verify Your Email', mail.outbox[0].subject)

    def test_verify_email_token_success(self):
        """Test successful email verification"""
        verification = EmailVerification.objects.create(user=self.user)
        
        success, message, user = verify_email_token(verification.token)
        
        self.assertTrue(success)
        self.assertEqual(user, self.user)
        self.assertTrue(user.email_verified)
        
        # Check that verification is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

    def test_verify_email_token_expired(self):
        """Test verification with expired token"""
        verification = EmailVerification.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        success, message, user = verify_email_token(verification.token)
        
        self.assertFalse(success)
        self.assertIn('expired', message.lower())
        self.assertIsNone(user)

    def test_verify_email_token_invalid(self):
        """Test verification with invalid token"""
        invalid_token = uuid.uuid4()
        
        success, message, user = verify_email_token(invalid_token)
        
        self.assertFalse(success)
        self.assertIn('invalid', message.lower())
        self.assertIsNone(user)

    def test_resend_verification_api(self):
        """Test resend verification API endpoint"""
        url = reverse('resend_verification')
        data = {'email': self.user.email}
        
        # Clear any existing mail
        mail.outbox = []
        
        response = self.client.post(url, data, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_verification_already_verified(self):
        """Test resend verification for already verified email"""
        self.user.email_verified = True
        self.user.save()
        
        url = reverse('resend_verification')
        data = {'email': self.user.email}
        
        response = self.client.post(url, data, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_check_email_verification_authenticated(self):
        """Test check email verification status for authenticated user"""
        self.client.force_login(self.user)
        url = reverse('check_email_verification')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['email_verified'], self.user.email_verified)

    def test_check_email_verification_unauthenticated(self):
        """Test check email verification status for unauthenticated user"""
        url = reverse('check_email_verification')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 401)

    def test_email_verification_view_success(self):
        """Test email verification view with valid token"""
        verification = EmailVerification.objects.create(user=self.user)
        url = reverse('verify_email', kwargs={'token': verification.token})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email Verified Successfully')
        
        # Check user is verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_email_verification_view_invalid_token(self):
        """Test email verification view with invalid token"""
        invalid_token = uuid.uuid4()
        url = reverse('verify_email', kwargs={'token': invalid_token})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Verification Failed')