from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import HandymanOrder, ServiceQuote, QuoteImage
from .serializers import (
    ServiceQuoteSerializer, ServiceQuoteCreateSerializer, 
    ServiceQuoteUpdateSerializer, HandymanOrderWithQuotesSerializer,
    QuoteImageSerializer
)
from accounts.permissions import IsHandler, IsAdmin


class ServiceProviderQuoteListView(generics.ListCreateAPIView):
    """
    List quotes for the authenticated service provider or create a new quote
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ServiceQuoteCreateSerializer
        return ServiceQuoteSerializer
    
    def get_queryset(self):
        """Return quotes for the authenticated service provider"""
        return ServiceQuote.objects.filter(
            service_provider=self.request.user
        ).select_related('handyman_order', 'service_provider')
    
    def perform_create(self, serializer):
        """Create a new quote"""
        handyman_order = serializer.validated_data['handyman_order']
        
        # Verify the user is assigned to this order
        if handyman_order.assistant != self.request.user:
            raise PermissionDenied("You can only create quotes for orders assigned to you")
        
        # Check if order status allows quote submission
        if handyman_order.status not in ['assigned', 'quote_rejected']:
            raise PermissionDenied("Cannot submit quote for this order status")
        
        serializer.save()


class ServiceProviderQuoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a quote (only for the quote owner)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceQuoteSerializer
    
    def get_queryset(self):
        return ServiceQuote.objects.filter(service_provider=self.request.user)
    
    def update(self, request, *args, **kwargs):
        quote = self.get_object()
        
        # Only allow updates if quote is in draft status
        if quote.status != 'draft':
            return Response(
                {'error': 'Can only update quotes in draft status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)


class SubmitQuoteView(APIView):
    """
    Submit a quote for review
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, quote_id):
        quote = get_object_or_404(ServiceQuote, id=quote_id, service_provider=request.user)
        
        if quote.status != 'draft':
            return Response(
                {'error': 'Can only submit quotes in draft status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quote.submit_quote()
        
        return Response({
            'message': 'Quote submitted successfully',
            'quote': ServiceQuoteSerializer(quote).data
        })


class HandlerQuoteManagementView(generics.ListAPIView):
    """
    List all quotes for handlers to review
    """
    permission_classes = [IsHandler]
    serializer_class = ServiceQuoteSerializer
    
    def get_queryset(self):
        queryset = ServiceQuote.objects.select_related(
            'handyman_order', 'service_provider'
        ).order_by('-created_at')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by handyman order
        order_id = self.request.query_params.get('order_id')
        if order_id:
            queryset = queryset.filter(handyman_order_id=order_id)
        
        return queryset


class ApproveRejectQuoteView(APIView):
    """
    Approve or reject a quote (handlers only)
    """
    permission_classes = [IsHandler]
    
    def post(self, request, quote_id):
        quote = get_object_or_404(ServiceQuote, id=quote_id)
        action = request.data.get('action')  # 'approve' or 'reject'
        
        if action == 'approve':
            quote.approve_quote()
            message = 'Quote approved successfully'
        elif action == 'reject':
            reason = request.data.get('reason', '')
            quote.reject_quote(reason)
            message = 'Quote rejected successfully'
        else:
            return Response(
                {'error': 'Invalid action. Use "approve" or "reject"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'quote': ServiceQuoteSerializer(quote).data
        })


class HandymanOrderQuotesView(generics.RetrieveAPIView):
    """
    Get a handyman order with all its quotes
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HandymanOrderWithQuotesSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Different access levels based on user type
        if user.user_type == 'handler':
            return HandymanOrder.objects.all()
        elif user.user_type == 'assistant':
            return HandymanOrder.objects.filter(assistant=user)
        else:  # client
            return HandymanOrder.objects.filter(client=user)


class QuoteImageUploadView(generics.CreateAPIView):
    """
    Upload images for a quote
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuoteImageSerializer
    
    def perform_create(self, serializer):
        quote_id = self.kwargs.get('quote_id')
        quote = get_object_or_404(ServiceQuote, id=quote_id, service_provider=self.request.user)
        
        # Only allow image upload for draft quotes
        if quote.status != 'draft':
            raise PermissionDenied("Can only upload images for draft quotes")
        
        serializer.save(quote=quote)


class ServiceProviderDashboardView(APIView):
    """
    Dashboard view for service providers showing their orders and quotes
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get assigned orders
        assigned_orders = HandymanOrder.objects.filter(
            assistant=user
        ).select_related('service_type', 'client')
        
        # Get quotes statistics
        quotes = ServiceQuote.objects.filter(service_provider=user)
        
        # Orders requiring quotes
        orders_needing_quotes = assigned_orders.filter(
            status__in=['assigned', 'quote_rejected']
        )
        
        # Orders with pending quotes
        orders_with_pending_quotes = assigned_orders.filter(
            status='quote_provided'
        )
        
        # Approved orders ready to start
        approved_orders = assigned_orders.filter(
            status='quote_approved'
        )
        
        dashboard_data = {
            'orders_needing_quotes': HandymanOrderWithQuotesSerializer(
                orders_needing_quotes, many=True, context={'request': request}
            ).data,
            'orders_with_pending_quotes': HandymanOrderWithQuotesSerializer(
                orders_with_pending_quotes, many=True, context={'request': request}
            ).data,
            'approved_orders': HandymanOrderWithQuotesSerializer(
                approved_orders, many=True, context={'request': request}
            ).data,
            'statistics': {
                'total_assigned_orders': assigned_orders.count(),
                'orders_needing_quotes': orders_needing_quotes.count(),
                'pending_quotes': quotes.filter(status='submitted').count(),
                'approved_quotes': quotes.filter(status='approved').count(),
                'rejected_quotes': quotes.filter(status='rejected').count(),
            }
        }
        
        return Response(dashboard_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def quote_status_check(request, order_id):
    """
    Check if a service provider can submit a quote for an order
    """
    try:
        order = HandymanOrder.objects.get(id=order_id)
        
        # Check if user is assigned to this order
        if order.assistant != request.user:
            return Response({
                'can_submit_quote': False,
                'reason': 'Not assigned to this order'
            })
        
        # Check order status
        if order.status not in ['assigned', 'quote_rejected']:
            return Response({
                'can_submit_quote': False,
                'reason': f'Order status is {order.get_status_display()}'
            })
        
        # Check if there's already a pending quote
        existing_quote = ServiceQuote.objects.filter(
            handyman_order=order,
            service_provider=request.user,
            status__in=['draft', 'submitted']
        ).first()
        
        if existing_quote:
            return Response({
                'can_submit_quote': False,
                'reason': 'You already have a pending quote for this order',
                'existing_quote_id': existing_quote.id,
                'existing_quote_status': existing_quote.status
            })
        
        return Response({
            'can_submit_quote': True,
            'order_details': {
                'id': order.id,
                'service_type': order.service_type.get_name_display(),
                'description': order.description,
                'address': order.address,
                'scheduled_date': order.scheduled_date,
                'scheduled_time_slot': order.get_scheduled_time_slot_display()
            }
        })
        
    except HandymanOrder.DoesNotExist:
        return Response(
            {'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )