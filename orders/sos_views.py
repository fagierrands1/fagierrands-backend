from rest_framework import serializers, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import EmergencyAlert, Order

class CreateSosSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    message = serializers.CharField(required=False, allow_blank=True, max_length=255)

class SosCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Only assistants
        if getattr(request.user, 'user_type', 'user') != 'assistant':
            return Response({'error': 'Only assistants can raise SOS'}, status=403)

        data = CreateSosSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        order = get_object_or_404(Order, pk=data.validated_data['order_id'])

        # Must be active and assigned to this assistant
        if order.status not in ['assigned', 'in_progress']:
            return Response({'error': 'SOS allowed only for active orders'}, status=400)
        if not order.assistant_id or order.assistant_id != request.user.id:
            return Response({'error': 'You are not assigned to this order'}, status=403)

        # Cooldown: 1 SOS per 2 minutes per assistant
        recent = EmergencyAlert.objects.filter(
            assistant=request.user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=2)
        )
        if recent.exists():
            return Response({'error': 'Please wait before sending another SOS'}, status=429)

        alert = EmergencyAlert.objects.create(
            assistant=request.user,
            order=order,
            latitude=data.validated_data.get('latitude'),
            longitude=data.validated_data.get('longitude'),
            message=data.validated_data.get('message', ''),
        )

        # TODO: Push notification to handlers/admins
        return Response({'id': alert.id, 'status': alert.status}, status=status.HTTP_201_CREATED)

class SosListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'user_type', 'user') not in ['handler', 'admin']:
            return Response({'error': 'Not allowed'}, status=403)
        qs = EmergencyAlert.objects.select_related('assistant', 'order').order_by('-created_at')[:200]
        results = []
        for a in qs:
            results.append({
                'id': a.id,
                'assistant': a.assistant.username if a.assistant_id else None,
                'assistant_id': a.assistant_id,
                'order_id': a.order_id,
                'latitude': a.latitude,
                'longitude': a.longitude,
                'message': a.message,
                'status': a.status,
                'created_at': a.created_at,
            })
        return Response({'results': results})

class SosResolveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, alert_id: int):
        if getattr(request.user, 'user_type', 'user') not in ['handler', 'admin']:
            return Response({'error': 'Not allowed'}, status=403)
        alert = get_object_or_404(EmergencyAlert, pk=alert_id)
        if alert.status == 'resolved':
            return Response({'id': alert.id, 'status': alert.status})
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save(update_fields=['status', 'resolved_by', 'resolved_at'])
        return Response({'id': alert.id, 'status': alert.status})