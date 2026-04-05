from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models_updated import (
    OrderTracking, ClientFeedback, RiderFeedback, CargoPhoto, CargoValue,
    ReportIssue, Referral, TrackingWaypoint, TrackingEvent, TrackingLocationHistory
)
from .serializers_updated import (
    OrderTrackingSerializer, OrderTrackingUpdateSerializer, OrderTrackingDetailSerializer,
    TrackingWaypointSerializer, TrackingEventSerializer, TrackingLocationHistorySerializer,
    ClientFeedbackSerializer, RiderFeedbackSerializer,
    CargoPhotoSerializer, CargoValueSerializer, ReportIssueSerializer, ReferralSerializer
)
from accounts.permissions import IsClient, IsAssistant, IsHandler, IsAdmin
from django.shortcuts import get_object_or_404
from .models import Order
from locations.models import UserLocation

class OrderTrackingView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating order tracking information
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get('pk')
        order = get_object_or_404(Order, id=order_id)
        
        # Check permissions
        user = self.request.user
        if user.user_type == 'user' and order.client != user:
            self.permission_denied(self.request)
        elif user.user_type == 'assistant' and order.assistant != user:
            self.permission_denied(self.request)
            
        # Get or create tracking object
        tracking, created = OrderTracking.objects.get_or_create(order=order)
        return tracking
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrderTrackingDetailSerializer
        return OrderTrackingUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only assistants can update tracking
        if request.user.user_type != 'assistant' or instance.order.assistant != request.user:
            return Response(
                {"detail": "Only the assigned assistant can update tracking information."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Create location history entry
        if 'current_latitude' in request.data and 'current_longitude' in request.data:
            TrackingLocationHistory.objects.create(
                tracking=instance,
                latitude=request.data['current_latitude'],
                longitude=request.data['current_longitude']
            )
        
        return Response(OrderTrackingDetailSerializer(instance).data)

class ClientFeedbackCreateView(generics.CreateAPIView):
    serializer_class = ClientFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.client != self.request.user:
            raise ValidationError("You can only submit feedback for your own orders.")
        serializer.save()

class ClientFeedbackDetailView(generics.RetrieveAPIView):
    serializer_class = ClientFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def get_queryset(self):
        user = self.request.user
        return ClientFeedback.objects.filter(order__client=user)

class RiderFeedbackCreateView(generics.CreateAPIView):
    serializer_class = RiderFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistant]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.assistant != self.request.user:
            raise ValidationError("You can only submit feedback for your assigned orders.")
        serializer.save()

class RiderFeedbackDetailView(generics.RetrieveAPIView):
    serializer_class = RiderFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistant]

    def get_queryset(self):
        user = self.request.user
        return RiderFeedback.objects.filter(order__assistant=user)

class CargoPhotoUploadView(generics.CreateAPIView):
    serializer_class = CargoPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        user = self.request.user
        if user.user_type == 'user' and order.client == user:
            serializer.save()
        elif user.user_type in ['handler', 'admin']:
            serializer.save()
        else:
            raise ValidationError("You do not have permission to upload cargo photos for this order.")

class CargoValueView(generics.RetrieveUpdateAPIView):
    serializer_class = CargoValueSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]

    def get_queryset(self):
        return CargoValue.objects.all()

class ReportIssueCreateView(generics.CreateAPIView):
    serializer_class = ReportIssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.client != self.request.user:
            raise ValidationError("You can only report issues for your own orders.")
        # Validate 24-hour report window
        if (timezone.now() - order.created_at).total_seconds() > 86400:
            raise ValidationError("Reports must be made within 24 hours of the order being placed.")
        serializer.save()

class ReportIssueListView(generics.ListAPIView):
    serializer_class = ReportIssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]

    def get_queryset(self):
        return ReportIssue.objects.all()

class ReferralCreateView(generics.CreateAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        referrer = self.request.user
        referred_user = serializer.validated_data['referred_user']
        if referrer == referred_user:
            raise ValidationError("You cannot refer yourself.")
        serializer.save(referrer=referrer)

class ReferralListView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)

class TrackingWaypointListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating waypoints
    """
    serializer_class = TrackingWaypointSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tracking_id = self.kwargs.get('tracking_id')
        return TrackingWaypoint.objects.filter(tracking_id=tracking_id)
    
    def perform_create(self, serializer):
        tracking_id = self.kwargs.get('tracking_id')
        tracking = get_object_or_404(OrderTracking, id=tracking_id)
        
        # Only assistants and handlers can create waypoints
        user = self.request.user
        if (user.user_type == 'assistant' and tracking.order.assistant == user) or \
           user.user_type in ['handler', 'admin']:
            serializer.save(tracking=tracking)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to create waypoints for this order.")

class TrackingWaypointDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating and deleting waypoints
    """
    serializer_class = TrackingWaypointSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TrackingWaypoint.objects.all()
    
    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        
        # Only assistants and handlers can modify waypoints
        user = request.user
        if not ((user.user_type == 'assistant' and obj.tracking.order.assistant == user) or \
                user.user_type in ['handler', 'admin']):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to modify this waypoint.")

class TrackingEventListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating tracking events
    """
    serializer_class = TrackingEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tracking_id = self.kwargs.get('tracking_id')
        return TrackingEvent.objects.filter(tracking_id=tracking_id)
    
    def perform_create(self, serializer):
        tracking_id = self.kwargs.get('tracking_id')
        tracking = get_object_or_404(OrderTracking, id=tracking_id)
        
        # Only assistants and handlers can create events
        user = self.request.user
        if (user.user_type == 'assistant' and tracking.order.assistant == user) or \
           user.user_type in ['handler', 'admin']:
            serializer.save(tracking=tracking)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to create events for this order.")

class TrackingEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating and deleting tracking events
    """
    serializer_class = TrackingEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TrackingEvent.objects.all()
    
    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        
        # Only assistants and handlers can modify events
        user = request.user
        if not ((user.user_type == 'assistant' and obj.tracking.order.assistant == user) or \
                user.user_type in ['handler', 'admin']):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to modify this event.")

class TrackingLocationHistoryListView(generics.ListAPIView):
    """
    API endpoint for listing location history
    """
    serializer_class = TrackingLocationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tracking_id = self.kwargs.get('tracking_id')
        tracking = get_object_or_404(OrderTracking, id=tracking_id)
        
        # Check permissions
        user = self.request.user
        if user.user_type == 'user' and tracking.order.client != user:
            return TrackingLocationHistory.objects.none()
        elif user.user_type == 'assistant' and tracking.order.assistant != user:
            return TrackingLocationHistory.objects.none()
            
        return TrackingLocationHistory.objects.filter(tracking_id=tracking_id)

class InitializeTrackingView(APIView):
    """
    Initialize tracking for an order when assigned to an assistant
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            order = get_object_or_404(Order, id=pk)
            
            # Only assistants can initialize tracking for their assigned orders
            if request.user.user_type != 'assistant' or order.assistant != request.user:
                return Response(
                    {"detail": "Only the assigned assistant can initialize tracking."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create tracking object
            tracking, created = OrderTracking.objects.get_or_create(order=order)
            
            # Get assistant's current location
            try:
                user_location = UserLocation.objects.get(user=request.user)
                
                # Update tracking with current location
                tracking.current_latitude = user_location.latitude
                tracking.current_longitude = user_location.longitude
                tracking.save()
                
                # Create initial location history entry
                TrackingLocationHistory.objects.create(
                    tracking=tracking,
                    latitude=user_location.latitude,
                    longitude=user_location.longitude
                )
                
                # Create waypoints from order locations
                if order.pickup_latitude and order.pickup_longitude:
                    TrackingWaypoint.objects.get_or_create(
                        tracking=tracking,
                        waypoint_type='pickup',
                        defaults={
                            'latitude': order.pickup_latitude,
                            'longitude': order.pickup_longitude,
                            'name': order.pickup_address or 'Pickup Location',
                            'order_index': 0
                        }
                    )
                
                if order.delivery_latitude and order.delivery_longitude:
                    TrackingWaypoint.objects.get_or_create(
                        tracking=tracking,
                        waypoint_type='delivery',
                        defaults={
                            'latitude': order.delivery_latitude,
                            'longitude': order.delivery_longitude,
                            'name': order.delivery_address or 'Delivery Location',
                            'order_index': 1
                        }
                    )
                
                # Create initial tracking event
                TrackingEvent.objects.create(
                    tracking=tracking,
                    event_type='pickup_started',
                    description='Assistant started tracking for this order',
                    latitude=user_location.latitude,
                    longitude=user_location.longitude
                )
                
                return Response({
                    "message": "Tracking initialized successfully",
                    "tracking_id": tracking.id,
                    "current_latitude": tracking.current_latitude,
                    "current_longitude": tracking.current_longitude
                }, status=status.HTTP_200_OK)
                
            except UserLocation.DoesNotExist:
                return Response(
                    {"detail": "Assistant location not found. Please update your location first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"detail": f"Error initializing tracking: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


