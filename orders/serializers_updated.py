from rest_framework import serializers
from .models_updated import (
    OrderTracking, ClientFeedback, RiderFeedback, CargoPhoto, CargoValue,
    ReportIssue, Referral, OrderVideo, TrackingWaypoint, TrackingEvent, TrackingLocationHistory
)

class TrackingWaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingWaypoint
        fields = [
            'id', 'tracking', 'latitude', 'longitude', 'waypoint_type', 
            'name', 'description', 'arrival_time', 'departure_time', 'order_index'
        ]
        read_only_fields = ['id']

class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = [
            'id', 'tracking', 'event_type', 'timestamp', 
            'latitude', 'longitude', 'description'
        ]
        read_only_fields = ['id', 'timestamp']

class TrackingLocationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingLocationHistory
        fields = ['id', 'tracking', 'latitude', 'longitude', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class OrderTrackingSerializer(serializers.ModelSerializer):
    waypoints = TrackingWaypointSerializer(many=True, read_only=True)
    events = TrackingEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = [
            'id', 'order', 'current_latitude', 'current_longitude', 
            'last_updated', 'estimated_arrival_time', 'waypoints', 'events'
        ]
        read_only_fields = ['id', 'last_updated']

class OrderTrackingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ['current_latitude', 'current_longitude', 'estimated_arrival_time']

class OrderTrackingDetailSerializer(serializers.ModelSerializer):
    waypoints = TrackingWaypointSerializer(many=True, read_only=True)
    events = TrackingEventSerializer(many=True, read_only=True)
    location_history = TrackingLocationHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = [
            'id', 'order', 'current_latitude', 'current_longitude', 
            'last_updated', 'estimated_arrival_time', 'waypoints', 
            'events', 'location_history'
        ]
        read_only_fields = ['id', 'last_updated']

class ClientFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientFeedback
        fields = ['order', 'delivered_promptly', 'professionalism', 'service_quality', 'comments', 'created_at']
        read_only_fields = ['created_at']

class RiderFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiderFeedback
        fields = ['order', 'clear_communication', 'payment_timeliness', 'interaction_quality', 'comments', 'created_at']
        read_only_fields = ['created_at']

class CargoPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoPhoto
        fields = ['id', 'order', 'photo', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class CargoValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoValue
        fields = ['order', 'value', 'visible_to_handler_only']

class OrderVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVideo
        fields = ['id', 'order', 'video', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class ReportIssueSerializer(serializers.ModelSerializer):
    evidence_photos = CargoPhotoSerializer(many=True, read_only=True)
    evidence_videos = OrderVideoSerializer(many=True, read_only=True)

    class Meta:
        model = ReportIssue
        fields = ['id', 'order', 'description', 'incident_timestamp', 'evidence_photos', 'evidence_videos', 'reported_at']
        read_only_fields = ['reported_at']

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ['id', 'referrer', 'referred_user', 'discount_amount', 'created_at', 'redeemed', 'redeemed_at']
        read_only_fields = ['created_at', 'redeemed_at']
