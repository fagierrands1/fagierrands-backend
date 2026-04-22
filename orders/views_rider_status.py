from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Order


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description='Order rider status',
            examples={
                'application/json': {
                    'finding_rider': {
                        'order_id': 13,
                        'status': 'pending',
                        'rider_status': 'finding_rider',
                        'message': 'Finding you a rider...',
                        'elapsed_time': {
                            'seconds': 45,
                            'minutes': 0,
                            'formatted': '0m 45s'
                        },
                        'max_wait_time_minutes': 5
                    },
                    'rider_found': {
                        'order_id': 13,
                        'status': 'assigned',
                        'rider_status': 'rider_found',
                        'message': 'Rider found!',
                        'rider': {
                            'id': 5,
                            'name': 'Mike Rider',
                            'phone_number': '+254712345678',
                            'plate_number': 'KCA 123X',
                            'profile_picture': 'https://example.com/profile.jpg'
                        },
                        'assigned_at': '2026-04-22T07:09:14.256793Z'
                    }
                }
            }
        ),
        404: 'Order not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_rider_status(request, order_id):
    """
    Get order status with rider details for client.
    
    Returns:
    - If status is 'pending': "finding_rider" with elapsed time
    - If status is 'assigned': "rider_found" with rider details
    - Otherwise: current status
    """
    try:
        order = Order.objects.select_related(
            'assistant', 'assistant__profile'
        ).get(id=order_id, client=request.user)
        
        response_data = {
            'order_id': order.id,
            'status': order.status,
        }
        
        if order.status == 'pending':
            # Finding rider phase
            elapsed_seconds = (timezone.now() - order.created_at).total_seconds()
            elapsed_minutes = int(elapsed_seconds // 60)
            
            response_data.update({
                'rider_status': 'finding_rider',
                'message': 'Finding you a rider...',
                'elapsed_time': {
                    'seconds': int(elapsed_seconds),
                    'minutes': elapsed_minutes,
                    'formatted': f"{elapsed_minutes}m {int(elapsed_seconds % 60)}s"
                },
                'max_wait_time_minutes': 5
            })
            
        elif order.status == 'assigned' and order.assistant:
            # Rider found
            rider = order.assistant
            profile = getattr(rider, 'profile', None)
            
            response_data.update({
                'rider_status': 'rider_found',
                'message': 'Rider found!',
                'rider': {
                    'id': rider.id,
                    'name': f"{rider.first_name} {rider.last_name}".strip() or rider.username,
                    'phone_number': rider.phone_number or 'N/A',
                    'plate_number': profile.plate_number if profile else None,
                    'profile_picture': profile.profile_picture_url if profile else None,
                },
                'assigned_at': order.assigned_at.isoformat() if order.assigned_at else None,
            })
            
        else:
            # Other statuses
            response_data.update({
                'rider_status': order.status,
                'message': f"Order is {order.get_status_display()}"
            })
        
        return Response(response_data)
        
    except Order.DoesNotExist:
        return Response({
            'error': 'Order not found or you do not have permission'
        }, status=status.HTTP_404_NOT_FOUND)
