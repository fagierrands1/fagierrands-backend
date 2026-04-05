from rest_framework import serializers
from .models import Location, UserLocation, Waypoint, RouteCalculation

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude', 'address', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # If this is the first location for the user, mark it as default
        if validated_data.get('is_default'):
            Location.objects.filter(user=user, is_default=True).update(is_default=False)
            
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Handle 'is_default' flag change
        if validated_data.get('is_default'):
            Location.objects.filter(user=instance.user, is_default=True).update(is_default=False)
            
        return super().update(instance, validated_data)

class UserLocationSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    user_type = serializers.ReadOnlyField(source='user.user_type')
    
    class Meta:
        model = UserLocation
        fields = ['id', 'user_id', 'username', 'user_type', 'latitude', 'longitude', 'heading', 'speed', 'accuracy', 'last_updated']
        read_only_fields = ['id', 'user_id', 'username', 'user_type', 'last_updated']

class WaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waypoint
        fields = [
            'id', 'order', 'name', 'description', 'latitude', 'longitude', 
            'address', 'waypoint_type', 'order_index', 'is_visited', 
            'visited_at', 'estimated_arrival_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'visited_at']
    
    def validate(self, data):
        """
        Validate that the waypoint coordinates are valid
        """
        if 'latitude' in data and (data['latitude'] < -90 or data['latitude'] > 90):
            raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90"})
        
        if 'longitude' in data and (data['longitude'] < -180 or data['longitude'] > 180):
            raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180"})
        
        return data

class RouteCalculationSerializer(serializers.ModelSerializer):
    start_waypoint_name = serializers.ReadOnlyField(source='start_waypoint.name')
    end_waypoint_name = serializers.ReadOnlyField(source='end_waypoint.name')
    
    class Meta:
        model = RouteCalculation
        fields = [
            'id', 'order', 'start_waypoint', 'end_waypoint', 
            'start_waypoint_name', 'end_waypoint_name',
            'distance', 'duration', 'route_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']