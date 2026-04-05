from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings
from .models import Profile, AssistantVerification, EmailVerification, EmailOTP
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer,
    AssistantVerificationSerializer, VerificationStatusSerializer,
    ChangePasswordSerializer, AssistantDetailSerializer,
    EmailVerificationSerializer, ResendVerificationSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
from .email_utils import send_verification_email, verify_email_token, resend_verification_email
from .supabase_client import get_supabase_client
from .permissions import IsOwnerOrReadOnly, IsHandler, IsAdmin
import json
import logging

logger = logging.getLogger(__name__)



User = get_user_model()

@api_view(['GET', 'OPTIONS'])
@permission_classes([permissions.AllowAny])
def debug_info(request):
    """
    Debug endpoint to check if the server is working correctly.
    """
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = Response({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "86400"  # 24 hours
        return response
        
    try:
        from django.conf import settings
        import sys
        
        # Collect debug information
        debug_data = {
            'status': 'ok',
            'message': 'Server is running',
            'python_version': sys.version,
            'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'unknown',
            'debug_mode': settings.DEBUG,
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'installed_apps': settings.INSTALLED_APPS,
            'auth_user_model': settings.AUTH_USER_MODEL,
            'authentication_backends': settings.AUTHENTICATION_BACKENDS,
            'request_meta': {k: str(v) for k, v in request.META.items() if k.startswith('HTTP_')},
            'cors_settings': {
                'CORS_ALLOW_ALL_ORIGINS': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', None),
                'CORS_ALLOWED_ORIGINS': getattr(settings, 'CORS_ALLOWED_ORIGINS', None),
                'CORS_ORIGIN_WHITELIST': getattr(settings, 'CORS_ORIGIN_WHITELIST', None),
                'CORS_ORIGIN_REGEX_WHITELIST': getattr(settings, 'CORS_ORIGIN_REGEX_WHITELIST', None),
            }
        }
        
        response = Response(debug_data)
        response["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        response = Response({
            'status': 'error',
            'message': f'Error collecting debug info: {str(e)}'
        }, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response

@csrf_exempt
def simple_login(request):
    """
    A simplified login endpoint that doesn't use JWT tokens for testing purposes.
    """
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "86400"  # 24 hours
        return response
        
    if request.method != 'POST':
        response = JsonResponse({'error': 'Only POST method is allowed'}, status=405)
        response["Access-Control-Allow-Origin"] = "*"
        return response
    
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            print("simple_login: Invalid JSON in request body")
            response = JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
            response["Access-Control-Allow-Origin"] = "*"
            return response
            
        email = data.get('email')
        password = data.get('password')
        
        print(f"simple_login: Login attempt for email: {email}")
        
        if not email or not password:
            response = JsonResponse({'error': 'Please provide both email and password'}, status=400)
            response["Access-Control-Allow-Origin"] = "*"
            return response
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response = JsonResponse({'error': 'No account found with this email'}, status=404)
            response["Access-Control-Allow-Origin"] = "*"
            return response
        except User.MultipleObjectsReturned:
            print(f"simple_login: Multiple users found with email: {email}")
            # Handle duplicate email case - get the most recently created one
            users = User.objects.filter(email=email).order_by('-date_joined')
            user = users.first()
            print(f"simple_login: Using most recent user with email {email}")
            print(f"simple_login: Warning: Found {users.count()} users with same email")
        
        user_auth = authenticate(username=user.username, password=password)
        
        if user_auth is not None:
            # Create a simple token (not JWT)
            import uuid
            simple_token = str(uuid.uuid4())
            
            # Return user info
            response = JsonResponse({
                'token': simple_token,
                'user_id': user.id,
                'email': user.email,
                'user_type': getattr(user, 'user_type', 'user'),
                'is_verified': getattr(user, 'is_verified', False),
                'email_verified': getattr(user, 'email_verified', False),
                'message': 'Login successful'
            })
            response["Access-Control-Allow-Origin"] = "*"
            return response
        else:
            response = JsonResponse({'error': 'Invalid credentials'}, status=401)
            response["Access-Control-Allow-Origin"] = "*"
            return response
    
    except Exception as e:
        print(f"simple_login: Error: {str(e)}")
        import traceback
        traceback.print_exc()
        response = JsonResponse({'error': f'Login error: {str(e)}'}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def options(self, request, *args, **kwargs):
        response = Response({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "86400"  # 24 hours
        return response
    
    def post(self, request):
        try:
            print("LoginView: Received login request")
            
            # Handle JSON parsing errors gracefully
            try:
                email = request.data.get('email')
                password = request.data.get('password')
            except ParseError as e:
                print(f"LoginView: JSON parse error: {str(e)}")
                return Response({"error": "Invalid JSON format in request body"}, 
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"LoginView: Data parsing error: {str(e)}")
                return Response({"error": "Error parsing request data"}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            print(f"LoginView: Login attempt for email: {email}")
            
            if not email or not password:
                print("LoginView: Missing email or password")
                return Response({"error": "Please provide both email and password"}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Try to find user by email since login form uses email
            try:
                print(f"LoginView: Looking up user with email: {email}")
                user = User.objects.get(email=email)
                username = user.username
                print(f"LoginView: Found user with email {email}, username: {username}")
            except User.DoesNotExist:
                print(f"LoginView: No user found with email: {email}")
                return Response({"error": "No account found with this email"}, 
                                status=status.HTTP_404_NOT_FOUND)
            except User.MultipleObjectsReturned:
                print(f"LoginView: Multiple users found with email: {email}")
                # Handle duplicate email case - get the most recently created one
                users = User.objects.filter(email=email).order_by('-date_joined')
                user = users.first()
                username = user.username
                print(f"LoginView: Using most recent user with email {email}, username: {username}")
                print(f"LoginView: Warning: Found {users.count()} users with same email - this should be investigated")
            except Exception as lookup_error:
                print(f"LoginView: Error looking up user: {str(lookup_error)}")
                return Response({"error": "Error looking up user account"}, 
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Authenticate with username (which could be the Supabase UID or a regular username)
            print(f"LoginView: Attempting to authenticate user: {username}")
            try:
                user = authenticate(username=username, password=password)
            except Exception as auth_error:
                print(f"LoginView: Authentication error: {str(auth_error)}")
                return Response({"error": f"Authentication error: {str(auth_error)}"}, 
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if user is not None:
                print(f"LoginView: Authentication successful for user: {username}")
                
                # Generate tokens
                try:
                    print("LoginView: Generating JWT token")
                    refresh = RefreshToken.for_user(user)
                    print("LoginView: JWT token generated successfully")
                except Exception as token_error:
                    print(f"LoginView: Error generating token: {str(token_error)}")
                    return Response({"error": f"Error generating authentication token: {str(token_error)}"}, 
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Update last login time
                try:
                    print("LoginView: Updating last login time")
                    user.last_login = timezone.now()
                    user.save()
                    print("LoginView: Last login time updated")
                except Exception as save_error:
                    print(f"LoginView: Error updating last login time: {str(save_error)}")
                    # Continue anyway since we have the token
                
                # Prepare response data with error handling for missing fields
                try:
                    print("LoginView: Preparing response data")
                    response_data = {
                        'token': str(refresh.access_token),
                        'refresh': str(refresh),
                        'user_id': user.id,
                        'email': user.email,
                    }
                    
                    # Safely add optional fields
                    if hasattr(user, 'user_type'):
                        response_data['user_type'] = user.user_type
                    else:
                        print("LoginView: Warning: user_type field not found on User model")
                        response_data['user_type'] = 'user'  # Default value
                        
                    if hasattr(user, 'is_verified'):
                        response_data['is_verified'] = user.is_verified
                    else:
                        print("LoginView: Warning: is_verified field not found on User model")
                        response_data['is_verified'] = False  # Default value
                        
                    if hasattr(user, 'email_verified'):
                        response_data['email_verified'] = user.email_verified
                    else:
                        print("LoginView: Warning: email_verified field not found on User model")
                        response_data['email_verified'] = False  # Default value
                    
                    print(f"LoginView: Login successful, returning response")
                    return Response(response_data, status=status.HTTP_200_OK)
                except Exception as response_error:
                    print(f"LoginView: Error creating response: {str(response_error)}")
                    return Response({"error": f"Error creating login response: {str(response_error)}"}, 
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                print(f"LoginView: Authentication failed for username: {username}")
                return Response({"error": "Invalid credentials"}, 
                                status=status.HTTP_401_UNAUTHORIZED)
                                
        except ParseError as e:
            print(f"LoginView: Parse error: {str(e)}")
            return Response({"error": "Invalid request format"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            print(f"LoginView: Validation error: {str(e)}")
            return Response({"error": "Invalid request data"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"LoginView: Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({"error": "Internal server error occurred"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add this new view to your views.py file
class AssistantListView(generics.ListAPIView):
    """
    API endpoint to list all assistant users with detailed verification information
    """
    serializer_class = AssistantDetailSerializer
    permission_classes = [IsHandler]
    filterset_fields = ['is_verified']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['date_joined', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        """
        This view should return a list of all users with user_type='assistant'
        with their verification information prefetched for efficiency
        """
        queryset = User.objects.filter(user_type='assistant').select_related('verification')
        
        # Add filtering by verification status
        verification_status = self.request.query_params.get('verification_status', None)
        if verification_status:
            if verification_status == 'not_submitted':
                queryset = queryset.filter(verification__isnull=True)
            else:
                queryset = queryset.filter(verification__status=verification_status)
        
        # Add filtering by user role (rider/service_provider)
        user_role = self.request.query_params.get('user_role', None)
        if user_role:
            queryset = queryset.filter(verification__user_role=user_role)
        
        # Add filtering by service type for service providers
        service_type = self.request.query_params.get('service_type', None)
        if service_type:
            queryset = queryset.filter(
                verification__user_role='service_provider',
                verification__service__icontains=service_type
            )
        
        return queryset

class AssistantStatsView(APIView):
    """
    API endpoint to get assistant statistics for handlers
    """
    permission_classes = [IsHandler]
    
    def get(self, request):
        """
        Get statistics about assistants for quick overview
        """
        try:
            # Total assistants
            total_assistants = User.objects.filter(user_type='assistant').count()
            
            # Verification status breakdown
            verified_count = User.objects.filter(
                user_type='assistant',
                verification__status='verified'
            ).count()
            
            pending_count = User.objects.filter(
                user_type='assistant',
                verification__status='pending'
            ).count()
            
            rejected_count = User.objects.filter(
                user_type='assistant',
                verification__status='rejected'
            ).count()
            
            not_submitted_count = User.objects.filter(
                user_type='assistant',
                verification__isnull=True
            ).count()
            
            # Role breakdown
            riders_count = User.objects.filter(
                user_type='assistant',
                verification__user_role='rider'
            ).count()
            
            service_providers_count = User.objects.filter(
                user_type='assistant',
                verification__user_role='service_provider'
            ).count()
            
            # Service types breakdown (for service providers)
            from django.db.models import Count
            service_types = User.objects.filter(
                user_type='assistant',
                verification__user_role='service_provider',
                verification__service__isnull=False
            ).values('verification__service').annotate(
                count=Count('verification__service')
            ).order_by('-count')
            
            stats = {
                'total_assistants': total_assistants,
                'verification_status': {
                    'verified': verified_count,
                    'pending': pending_count,
                    'rejected': rejected_count,
                    'not_submitted': not_submitted_count
                },
                'roles': {
                    'riders': riders_count,
                    'service_providers': service_providers_count,
                    'unspecified': total_assistants - riders_count - service_providers_count
                },
                'service_types': [
                    {
                        'service': item['verification__service'],
                        'count': item['count']
                    }
                    for item in service_types
                ]
            }
            
            return Response(stats)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get assistant stats: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HandlerClientsView(APIView):
    """
    API endpoint for handlers to get their assigned clients
    Returns all clients where account_manager is set to the current handler
    """
    permission_classes = [IsHandler]
    
    def get(self, request):
        """
        Get all clients assigned to the current handler
        """
        try:
            handler = request.user
            
            # Verify user is a handler
            if handler.user_type != 'handler':
                return Response(
                    {'error': 'Only handlers can access this endpoint'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get all clients assigned to this handler
            clients = User.objects.filter(
                account_manager=handler,
                user_type__in=['user', 'client']
            ).order_by('-date_joined')
            
            # Serialize clients
            serializer = UserSerializer(clients, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f'Error fetching handler clients: {str(e)}')
            return Response(
                {'error': f'Failed to fetch clients: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def perform_create(self, serializer):
        """Create user and send OTP verification email"""
        user = serializer.save()
        
        # Send OTP verification email
        try:
            from .otp_utils import send_otp_email
            success, message = send_otp_email(user, self.request)
            if success:
                logger.info(f"OTP verification email sent to {user.email}")
            else:
                logger.error(f"Failed to send OTP email to {user.email}: {message}")
        except Exception as e:
            logger.error(f"Failed to send OTP verification email to {user.email}: {str(e)}")
            # Don't fail registration if email sending fails
            pass
    

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def supabase_user_creation(request):
    """
    Handle user creation from Supabase authentication.
    This endpoint should be called after a successful Supabase signup.
    """
    try:
        data = request.data
        supabase_uid = data.get('user_id')
        email = data.get('email')
        phone = data.get('phone', '')
        account_type = data.get('account_type', 'user').lower()
        
        # Check if user already exists with this UID or email
        if User.objects.filter(username=supabase_uid).exists():
            return Response({"message": "User already exists"}, status=status.HTTP_200_OK)
        
        # Check for duplicate email addresses
        if User.objects.filter(email=email).exists():
            return Response({
                "error": "User with this email already exists",
                "message": "An account with this email address already exists"
            }, status=status.HTTP_409_CONFLICT)
        
        # Map account type to your model's choices
        user_type_mapping = {
            'client': 'user',
            'assistant': 'assistant',
            'handler': 'handler',
            'admin': 'admin'
        }
        
        user_type = user_type_mapping.get(account_type, 'user')
        
        # Create user in Django with error handling for duplicates
        try:
            user = User.objects.create_user(
                username=supabase_uid,
                email=email,
                phone_number=phone,
                user_type=user_type,
                is_verified=False,
                email_verified=True  # Since Supabase handles email verification
            )
        except Exception as create_error:
            logger.error(f"Error creating user: {str(create_error)}")
            if "unique constraint" in str(create_error).lower() or "duplicate" in str(create_error).lower():
                return Response({
                    "error": "User with this email or username already exists",
                    "message": "An account with these details already exists"
                }, status=status.HTTP_409_CONFLICT)
            else:
                raise create_error
        
        # Create associated profile
        Profile.objects.create(user=user)
        
        return Response({
            "message": "User created successfully",
            "user_id": user.id,
            "email": user.email,
            "user_type": user.user_type
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def supabase_auth_webhook(request):
    """
    Handle Supabase auth webhooks for user events.
    Configure this in your Supabase dashboard under Auth > Webhooks.
    """
    try:
        event_type = request.data.get('type')
        event = request.data.get('event')
        
        if event_type == 'USER_CREATED':
            # Handle user creation
            user_data = event.get('user', {})
            supabase_uid = user_data.get('id')
            email = user_data.get('email')
            metadata = user_data.get('user_metadata', {})
            phone = metadata.get('phone', '')
            account_type = metadata.get('account_type', 'user').lower()
            
            # Map account type
            user_type_mapping = {
                'client': 'user', 
                'assistant': 'assistant',
                'handler': 'handler',
                'admin': 'admin'
            }
            
            user_type = user_type_mapping.get(account_type, 'user')
            
            # Create user if doesn't exist (check both UID and email)
            if not User.objects.filter(username=supabase_uid).exists() and not User.objects.filter(email=email).exists():
                try:
                    user = User.objects.create_user(
                        username=supabase_uid,
                        email=email,
                        phone_number=phone,
                        user_type=user_type,
                        is_verified=False,
                        email_verified=False
                    )
                    Profile.objects.create(user=user)
                    logger.info(f"User created via webhook: {email}")
                except Exception as create_error:
                    logger.error(f"Error creating user via webhook: {str(create_error)}")
                    # Don't return error - webhook should succeed even if user creation fails
            else:
                logger.info(f"User already exists, skipping creation: {email}")
        
        elif event_type == 'USER_DELETED':
            # Handle user deletion
            supabase_uid = event.get('user', {}).get('id')
            try:
                user = User.objects.get(username=supabase_uid)
                user.delete()
            except User.DoesNotExist:
                pass
                
        return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_supabase_token(request):
    """
    Validate a Supabase token and return Django user details
    """
    user = request.user
    return Response({
        "user_id": user.id,
        "email": user.email,
        "user_type": user.user_type,
        "is_verified": user.is_verified,
        "email_verified": user.email_verified
    })

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_object(self):
        return self.request.user

class UserByIdView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve a specific user by ID
    Handlers and admins can view any user, other users can only view themselves
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        requested_user_id = self.kwargs.get('pk')
        
        # If the user is requesting their own data, or is a handler/admin, allow access
        if (str(user.id) == str(requested_user_id) or 
            user.user_type in ['handler', 'admin']):
            try:
                return User.objects.get(pk=requested_user_id)
            except User.DoesNotExist:
                raise Http404("User not found")
        else:
            # Otherwise, deny access
            raise PermissionDenied("You do not have permission to view this user's data")

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_object(self):
        return Profile.objects.get(user=self.request.user)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.data.get("new_password"))
            user.save()
            
            # Update password in Supabase (you would need to implement this)
            # This would require calling Supabase Admin API
            
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Note: Supabase token invalidation should be handled client-side
            # by removing the token from local storage
            
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"message": "If this email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

        # Generate a 6-digit OTP and email it
        otp = EmailOTP.generate_otp() if hasattr(EmailOTP, 'generate_otp') else None
        if not otp:
            from random import randint
            otp = str(randint(100000, 999999))

        EmailOTP.objects.create(user=user, otp_code=otp)

        # Send password reset email using proper SMTP utility
        try:
            from .otp_utils import send_password_reset_email
            success, message = send_password_reset_email(user, otp)
            if success:
                logger.info(f"Password reset OTP sent to {email}")
            else:
                logger.error(f"Failed to send reset OTP to {email}: {message}")
        except Exception as e:
            logger.error(f"Failed to send reset OTP to {email}: {e}")
            # Still return 200 to avoid email enumeration

        return Response({"message": "If this email exists, an OTP has been sent."}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Invalid reset request"}, status=status.HTTP_400_BAD_REQUEST)

        # Find unused, non-expired OTP
        otp = EmailOTP.objects.filter(user=user, otp_code=otp_code, is_used=False).order_by('-created_at').first()
        if not otp:
            return Response({"error": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)
        if otp.is_expired():
            return Response({"error": "Code expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user.set_password(new_password)
        user.save()

        # Mark OTP used
        otp.is_used = True
        otp.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that supports email login"""
    
    def validate(self, attrs):
        # Get the username and password from the request
        username_or_email = attrs.get('username')
        password = attrs.get('password')
        
        # Check if user provided email instead of username
        try:
            if '@' in username_or_email:
                # It's an email, find the user by email
                user = User.objects.get(email=username_or_email)
                attrs['username'] = user.username
            else:
                # It's a username, keep as is
                attrs['username'] = username_or_email
        except User.DoesNotExist:
            raise serializers.ValidationError('No account found with this email/username.')
        
        # Call the parent validate method
        return super().validate(attrs)


class TokenObtainPairView(TokenObtainPairView):
    """Custom token obtain pair view that supports email login"""
    serializer_class = CustomTokenObtainPairSerializer

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import AssistantVerification
from .serializers import (
    AssistantVerificationSerializer,
    VerificationStatusSerializer,
    VerificationStatusUpdateSerializer
)
from .permissions import IsHandler, IsAdmin

class AssistantVerificationView(generics.CreateAPIView):
    """
    API endpoint for assistants to submit verification documents
    """
    serializer_class = AssistantVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        """Override create to handle file uploads properly"""
        # Check if user is an assistant
        if request.user.user_type != 'assistant':
            return Response(
                {"error": "Only assistant accounts can submit verification"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Proceed with normal creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Update user verification status to pending
        user = request.user
        user.is_verified = False
        user.save()
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def perform_create(self, serializer):
        serializer.save()

class VerificationStatusView(generics.RetrieveAPIView):
    """
    API endpoint for assistants to check their verification status
    """
    serializer_class = VerificationStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get the verification object for the current user"""
        verification = AssistantVerification.objects.filter(user=self.request.user).first()
        if not verification:
            return Response(
                {"error": "No verification request found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return verification

class AssistantVerificationListView(generics.ListAPIView):
    """
    API endpoint for admins/handlers to view all verification requests
    """
    serializer_class = AssistantVerificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]
    
    def get_queryset(self):
        """
        Filter verifications based on status query parameter
        """
        queryset = AssistantVerification.objects.all()
        status_filter = self.request.query_params.get('status')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

class AssistantVerificationDetailView(generics.RetrieveAPIView):
    """
    API endpoint for admins/handlers to view a specific verification request
    """
    queryset = AssistantVerification.objects.all()
    serializer_class = AssistantVerificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]

class AssistantVerificationUpdateView(generics.UpdateAPIView):
    """
    API endpoint for admins/handlers to update verification status
    """
    queryset = AssistantVerification.objects.all()
    serializer_class = VerificationStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]
    
    def perform_update(self, serializer):
        """
        Custom logic when updating verification status
        """
        verification = serializer.save()
        
        # Update user verification status based on verification decision
        user = verification.user
        if verification.status == 'verified':
            user.is_verified = True
            # Set verification timestamp
            verification.verified_at = timezone.now()
            verification.save()
        else:
            user.is_verified = False
        
        user.save()
        
        return Response(serializer.data)

from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssistantVerification
from .serializers import AssistantVerificationSerializer
from .storage_utils import upload_verification_image

class AssistantVerificationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Check if user is an assistant
        if hasattr(user, 'user_type') and user.user_type != 'assistant':
            return Response(
                {"error": "Only assistant accounts can submit verification"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user already has a pending verification
        existing_verification = AssistantVerification.objects.filter(user=user).first()
        if existing_verification and existing_verification.status == 'pending':
            return Response({
                "detail": "You already have a pending verification request."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Extract form data
        user_role = request.data.get('user_role')
        full_name = request.data.get('full_name')
        id_number = request.data.get('id_number')
        area_of_operation = request.data.get('area_of_operation')
        phone_number = request.data.get('phone_number')
        years_of_experience = request.data.get('years_of_experience')
        
        # Role-specific data
        driving_license_number = None
        service = None
        
        if user_role == 'rider':
            driving_license_number = request.data.get('driving_license_number')
            if not driving_license_number:
                return Response({
                    "detail": "Driving license number is required for riders."
                }, status=status.HTTP_400_BAD_REQUEST)
        elif user_role == 'service_provider':
            service = request.data.get('service')
            if not service:
                return Response({
                    "detail": "Service type is required for service providers."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create verification object with basic data
        verification_data = {
            'user': user.id,
            'user_role': user_role,
            'full_name': full_name,
            'id_number': id_number,
            'area_of_operation': area_of_operation,
            'phone_number': phone_number,
            'years_of_experience': years_of_experience,
            'less_than_a_year_experience': years_of_experience == 'less_than_a_year',
            'status': 'pending',
        }
        
        if driving_license_number:
            verification_data['driving_license_number'] = driving_license_number
        
        if service:
            verification_data['service'] = service
        
        # Handle file uploads to Supabase with proper error handling
        image_fields = {
            'id_front': 'id_front_url',
            'id_back': 'id_back_url',
            'selfie': 'selfie_url',
            'driving_license_image': 'driving_license_url',
            'certificate_image': 'certificate_url'
        }
        
        # Process each image file
        for field_name, url_field in image_fields.items():
            image_file = request.FILES.get(field_name)
            
            # Skip optional fields based on user role
            if field_name == 'driving_license_image' and user_role != 'rider':
                continue
                
            if field_name == 'certificate_image' and user_role != 'service_provider':
                continue
                
            # Skip if no file uploaded for this field
            if not image_file:
                if field_name in ['id_front', 'id_back', 'selfie']:
                    return Response({
                        "detail": f"{field_name.replace('_', ' ').title()} is required."
                    }, status=status.HTTP_400_BAD_REQUEST)
                elif field_name == 'driving_license_image' and user_role == 'rider':
                    return Response({
                        "detail": "Driving license image is required for riders."
                    }, status=status.HTTP_400_BAD_REQUEST)
                elif field_name == 'certificate_image' and user_role == 'service_provider':
                    return Response({
                        "detail": "Certificate image is required for service providers."
                    }, status=status.HTTP_400_BAD_REQUEST)
                continue
            
            try:
                # Upload the image to Supabase with explicit auth
                logger.info(f"Uploading {field_name} for user {user.id}")
                success, result, error_message = upload_verification_image(
                    image_file, 
                    user.id, 
                    field_name
                )
                
                logger.info(f"Upload result for {field_name}: success={success}, result={result}, error={error_message}")
                
                if not success:
                    logger.error(f"Upload failed for {field_name}: {error_message}")
                    return Response({
                        "detail": f"Failed to upload {field_name}: {error_message}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                # Add the URL to verification data
                verification_data[url_field] = result
                logger.info(f"Added {url_field} = {result} to verification data")
                
            except Exception as e:
                logger.error(f"Exception uploading {field_name}: {str(e)}")
                return Response({
                    "detail": f"Error uploading {field_name}: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create or update verification
        serializer = AssistantVerificationSerializer(data=verification_data)
        if serializer.is_valid():
            # If existing verification exists, delete it first
            if existing_verification:
                existing_verification.delete()
                
            serializer.save()
            
            # Update user verification status
            user.is_verified = False
            user.save()
            
            return Response({
                "message": "Verification submitted successfully",
                "status": "pending",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    View to handle email verification via token
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """Handle email verification via GET request"""
        success, message, user = verify_email_token(token)
        
        if success:
            # Render success page
            context = {
                'success': True,
                'message': message,
                'user': user,
                'frontend_url': getattr(settings, 'FRONTEND_URL', 'https://fagierrands-x9ow.vercel.app')
            }
            return render(request, 'email_verified_success.html', context)
        else:
            # Render error page
            context = {
                'success': False,
                'message': message,
                'frontend_url': getattr(settings, 'FRONTEND_URL', 'https://fagierrands-x9ow.vercel.app')
            }
            return render(request, 'email_verified_success.html', context)


class ResendVerificationEmailView(APIView):
    """
    View to resend email verification
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendVerificationSerializer
    
    def post(self, request):
        """Resend verification email"""
        serializer = ResendVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            success, message = resend_verification_email(email, request)
            
            if success:
                return Response({
                    'success': True,
                    'message': message
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailOTPView(APIView):
    """
    View to verify email using OTP code
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify email using OTP code"""
        try:
            email = request.data.get('email')
            otp_code = request.data.get('otp_code')
            
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not otp_code:
                return Response({
                    'success': False,
                    'message': 'OTP code is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Import the verification function
            from .email_utils import verify_otp_code
            
            success, message, user = verify_otp_code(email, otp_code)
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'user_id': user.id if user else None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while verifying the code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupabaseResendVerificationView(APIView):
    """
    View to resend email verification using Supabase
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Resend verification email using Supabase"""
        try:
            email = request.data.get('email')
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get Supabase client
            supabase = get_supabase_client()
            if not supabase:
                return Response({
                    'success': False,
                    'message': 'Email service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check if user exists in Django
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No account found with this email address'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if email is already verified
            if user.email_verified:
                return Response({
                    'success': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use Supabase to send OTP email verification
            try:
                redirect_url = f"{settings.FRONTEND_URL}/auth/callback"
                logger.info(f"Sending OTP verification email to {email}")
                logger.info(f"Using redirect URL: {redirect_url}")
                
                # Use sign_in_with_otp (triggers "Magic Link" template)
                # We'll customize the "Magic Link" template to show OTP instead
                response = supabase.auth.sign_in_with_otp({
                    "email": email,
                    "options": {
                        "email_redirect_to": redirect_url,
                        "should_create_user": False
                    }
                })
                
                return Response({
                    'success': True,
                    'message': 'Verification email sent successfully via Supabase'
                }, status=status.HTTP_200_OK)
                
            except Exception as supabase_error:
                error_message = str(supabase_error)
                logger.error(f"Supabase resend error: {error_message}")
                
                # Check if it's a domain restriction error
                if "Signups not allowed for otp" in error_message:
                    return Response({
                        'success': False,
                        'message': 'Email domain not allowed. Please use a different email address or contact support.',
                        'error_type': 'domain_restricted'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'success': False,
                    'message': f'Failed to send verification email: {error_message}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Unexpected error in Supabase resend: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckEmailVerificationView(APIView):
    """
    View to check if user's email is verified
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Check if current user's email is verified"""
        user = request.user
        return Response({
            'email_verified': user.email_verified,
            'email': user.email
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def custom_resend_verification(request):
    """
    Custom resend verification that creates a link to your frontend
    """
    try:
        email = request.data.get('email')
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists in Django
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No account found with this email address'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if email is already verified
        if user.email_verified:
            return Response({
                'success': False,
                'message': 'Email is already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a verification token in Django
        from .models import EmailVerification
        import uuid
        
        # Delete any existing tokens for this user
        EmailVerification.objects.filter(user=user, is_used=False).delete()
        
        # Create new verification token
        verification = EmailVerification.objects.create(
            user=user,
            token=uuid.uuid4(),
            is_used=False
        )
        
        # Create verification URL that points to your frontend
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{verification.token}"
        
        # Send email using Django's email system
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        try:
            # Render email template
            email_subject = 'Verify Your Email Address - Fagi Errands'
            email_body = render_to_string('email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'frontend_url': settings.FRONTEND_URL
            })
            
            # Send email
            send_mail(
                subject=email_subject,
                message=f'Please verify your email by clicking this link: {verification_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=email_body,
                fail_silently=False
            )
            logger.info(f"Email sent successfully to {email}")
            
        except Exception as email_error:
            logger.error(f"Failed to send email: {str(email_error)}")
            # Return success anyway since we created the token
            return Response({
                'success': True,
                'message': 'Verification token created. Email sending failed but you can use the verification URL directly.',
                'verification_url': verification_url,
                'error': str(email_error)
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': True,
            'message': 'Verification email sent successfully',
            'verification_url': verification_url  # For testing purposes
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in custom resend verification: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to send verification email'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def supabase_verify_otp(request):
    """
    Verify OTP token from Supabase email
    """
    try:
        email = request.data.get('email')
        token = request.data.get('token')
        
        if not email or not token:
            return Response({
                'success': False,
                'message': 'Email and token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            return Response({
                'success': False,
                'message': 'Verification service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # Verify OTP with Supabase
            response = supabase.auth.verify_otp({
                "email": email,
                "token": token,
                "type": "email"
            })
            
            if response.user:
                # Update Django user's email_verified status
                try:
                    user = User.objects.get(email=email)
                    user.email_verified = True
                    user.save()
                    logger.info(f"Email verified successfully for user: {email}")
                    
                    return Response({
                        'success': True,
                        'message': 'Email verified successfully',
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'email_verified': user.email_verified
                        }
                    }, status=status.HTTP_200_OK)
                    
                except User.DoesNotExist:
                    logger.warning(f"User not found in Django for email: {email}")
                    return Response({
                        'success': False,
                        'message': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid or expired verification token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as supabase_error:
            logger.error(f"Supabase OTP verification error: {str(supabase_error)}")
            return Response({
                'success': False,
                'message': 'Invalid or expired verification token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Unexpected error in OTP verification: {str(e)}")
        return Response({
            'success': False,
            'message': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# OTP Verification Views
class SendOTPView(APIView):
    """
    View to send OTP verification email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send OTP verification email"""
        try:
            email = request.data.get('email')
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from .otp_utils import send_otp_email
            from .models import User
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No user found with this email address'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if user.email_verified:
                return Response({
                    'success': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            success, message = send_otp_email(user, request)
            
            if success:
                return Response({
                    'success': True,
                    'message': message
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while sending OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    """
    View to verify OTP code
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify OTP code"""
        try:
            email = request.data.get('email')
            otp_code = request.data.get('otp_code')
            
            if not email or not otp_code:
                return Response({
                    'success': False,
                    'message': 'Email and OTP code are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from .otp_utils import verify_otp
            
            success, message, user = verify_otp(email, otp_code)
            
            if success:
                return Response({
                    'success': True,
                    'message': message,
                    'user_id': user.id if user else None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while verifying OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendOTPView(APIView):
    """
    View to resend OTP verification email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Resend OTP verification email"""
        try:
            email = request.data.get('email')
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from .otp_utils import resend_otp_email
            
            success, message = resend_otp_email(email, request)
            
            if success:
                return Response({
                    'success': True,
                    'message': message
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error resending OTP: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while resending OTP'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OTPStatusView(APIView):
    """
    View to check OTP verification status
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get OTP verification status"""
        try:
            email = request.query_params.get('email')
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from .otp_utils import get_otp_status
            
            status_data = get_otp_status(email)
            
            return Response(status_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting OTP status: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while checking OTP status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# SMTP-Based Email Verification (No Domain Restrictions)
class SMTPSendOTPView(APIView):
    """
    Send OTP via SMTP email (bypasses Supabase domain restrictions)
    Uses Django's email system with custom SMTP backend
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email address is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                return Response({
                    'success': False,
                    'message': 'Invalid email address format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists - handle duplicate users
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No user found with this email address'
                }, status=status.HTTP_404_NOT_FOUND)
            except User.MultipleObjectsReturned:
                logger.warning(f"Multiple users found with email: {email}. Using most recent.")
                # Handle duplicate email case - get the most recently created one
                users = User.objects.filter(email=email).order_by('-date_joined')
                user = users.first()
                logger.info(f"Selected user ID {user.id} (most recent) for email {email}")
            
            # Check if already verified
            if user.email_verified:
                return Response({
                    'success': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate 6-digit OTP using the existing OTPVerification model
            from accounts.models import OTPVerification
            from datetime import timedelta
            import random
            
            otp_code = str(random.randint(100000, 999999))
            
            # Create new OTP record with expiration
            otp_record = OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=timezone.now() + timedelta(hours=1),
                is_used=False,
                attempts=0
            )
            
            # Send email via SMTP
            try:
                subject = 'Email Verification - Fagi Errands'
                
                # Create email content
                html_content = f'''
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="color: #333;">Email Verification - Fagi Errands</h2>
                    </div>
                    
                    <p>Hello {user.first_name or 'there'}!</p>
                    <p>Your email verification code is:</p>
                    
                    <div style="background: #f4f4f4; padding: 30px; text-align: center; margin: 30px 0; border-radius: 10px; border: 2px dashed #007bff;">
                        <h1 style="font-size: 48px; color: #007bff; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace; font-weight: bold;">
                            {otp_code}
                        </h1>
                    </div>
                    
                    <p><strong>Enter this 6-digit code in the app to verify your email address.</strong></p>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #856404;">
                            <strong>⏰ This code will expire in 1 hour.</strong>
                        </p>
                    </div>
                    
                    <p>If you didn't request this verification, please ignore this email.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    
                    <div style="text-align: center; color: #666; font-size: 14px;">
                        <p><strong>Fagi Errands</strong></p>
                        <p>Your trusted delivery service</p>
                        <p>🚚 Fast • Reliable • Affordable</p>
                    </div>
                </body>
                </html>
                '''
                
                # Plain text version
                text_content = f'''
                Email Verification - Fagi Errands
                
                Hello {user.first_name or 'there'}!
                
                Your email verification code is: {otp_code}
                
                Enter this 6-digit code in the app to verify your email address.
                
                This code will expire in 1 hour.
                
                If you didn't request this verification, please ignore this email.
                
                ---
                Fagi Errands - Your trusted delivery service
                '''
                
                # Send email
                from django.core.mail import EmailMultiAlternatives
                
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                logger.info(f"SMTP verification email sent to {email} with OTP: {otp_code}")
                
                return Response({
                    'success': True,
                    'message': 'Verification email sent successfully via SMTP!',
                    'method': 'smtp',
                    'expires_in': '1 hour'
                }, status=status.HTTP_200_OK)
                
            except Exception as email_error:
                logger.error(f"SMTP email sending error: {str(email_error)}")
                return Response({
                    'success': False,
                    'message': f'Failed to send email: {str(email_error)}',
                    'error_type': 'smtp_error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Unexpected error in SMTP OTP sending: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SMTPVerifyOTPView(APIView):
    """
    Verify OTP code sent via SMTP email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            token = request.data.get('token')
            email = request.data.get('email')
            
            if not token:
                return Response({
                    'success': False,
                    'message': 'OTP code is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Find OTP record
            try:
                from accounts.models import OTPVerification
                otp_record = OTPVerification.objects.get(
                    user=user,
                    otp_code=token,
                    is_used=False
                )
                
                # Check if OTP is expired
                if otp_record.is_expired():
                    return Response({
                        'success': False,
                        'message': 'OTP code has expired. Please request a new one.',
                        'error_type': 'expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if max attempts reached
                if otp_record.is_max_attempts_reached():
                    return Response({
                        'success': False,
                        'message': 'Maximum verification attempts reached. Please request a new OTP.',
                        'error_type': 'max_attempts'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Increment attempts
                otp_record.attempts += 1
                otp_record.save()
                
                # Mark OTP as used
                otp_record.is_used = True
                otp_record.save()
                
                # Mark user as verified
                user.email_verified = True
                user.save()
                
                logger.info(f"SMTP email verified successfully for user: {email}")
                
                return Response({
                    'success': True,
                    'message': 'Email verified successfully!',
                    'method': 'smtp',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'email_verified': user.email_verified
                    }
                }, status=status.HTTP_200_OK)
                
            except OTPVerification.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid OTP code. Please check and try again.',
                    'error_type': 'invalid_token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Unexpected error in SMTP OTP verification: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssistantDashboardStatsView(APIView):
    """
    API endpoint for individual assistant dashboard statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Only assistants can access their own dashboard stats
        if user.user_type != 'assistant':
            return Response({
                'error': 'Only assistants can access dashboard statistics'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Import Order model here to avoid circular imports
            from orders.models import Order
            
            # Get assistant's orders
            assistant_orders = Order.objects.filter(assistant=user)
            
            # Calculate statistics
            total_orders = assistant_orders.count()
            completed_orders = assistant_orders.filter(status='completed').count()
            in_progress_orders = assistant_orders.filter(status='in_progress').count()
            assigned_orders = assistant_orders.filter(status='assigned').count()
            
            # Calculate completion rate
            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            # Calculate total earnings (sum of completed orders)
            total_earnings = sum(
                float(order.price) for order in assistant_orders.filter(status='completed') 
                if order.price
            )
            
            # Get recent orders (last 5)
            recent_orders = assistant_orders.order_by('-created_at')[:5]
            recent_orders_data = []
            
            for order in recent_orders:
                recent_orders_data.append({
                    'id': order.id,
                    'title': order.title,
                    'status': order.status,
                    'price': float(order.price) if order.price else 0,
                    'created_at': order.created_at.isoformat(),
                    'order_type': order.order_type.name if order.order_type else 'Unknown'
                })
            
            return Response({
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'in_progress_orders': in_progress_orders,
                'assigned_orders': assigned_orders,
                'completion_rate': round(completion_rate, 1),
                'total_earnings': total_earnings,
                'recent_orders': recent_orders_data,
                'assistant_info': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching assistant dashboard stats: {str(e)}")
            return Response({
                'error': 'Failed to fetch dashboard statistics',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HandlerClientsView(generics.ListAPIView):
    """
    View for handlers to list their assigned clients
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler]
    
    def get_queryset(self):
        handler = self.request.user
        # Return clients where this handler is the account_manager
        return User.objects.filter(account_manager=handler, user_type='user').order_by('first_name', 'last_name')


class AssignAccountManagerView(generics.UpdateAPIView):
    """
    View for admins/handlers to assign account managers to clients
    """
    queryset = User.objects.filter(user_type='user')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        # Only admins and handlers can assign account managers
        if self.request.user.user_type in ['admin', 'handler']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        account_manager_id = request.data.get('account_manager_id')
        
        # Validate account_manager_id
        if account_manager_id is None:
            # Allow unassigning (setting to null)
            user.account_manager = None
            user.save()
            return Response({
                'success': True,
                'message': 'Account manager unassigned successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        try:
            account_manager = User.objects.get(id=account_manager_id, user_type='handler')
            user.account_manager = account_manager
            user.save()
            
            return Response({
                'success': True,
                'message': f'Account manager assigned successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Handler not found'
            }, status=status.HTTP_404_NOT_FOUND)