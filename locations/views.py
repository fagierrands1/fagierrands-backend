from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
import math
import requests
import os
import json
import logging

from .models import Location, UserLocation, Waypoint, RouteCalculation
from .serializers import (
    LocationSerializer, UserLocationSerializer, 
    WaypointSerializer, RouteCalculationSerializer
)
from accounts.permissions import IsOwnerOrReadOnly, IsHandler, IsAdmin, IsAssistant

User = get_user_model()

class LocationListCreateView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Location.objects.filter(user=self.request.user)

class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Location.objects.filter(user=self.request.user)

class SetDefaultLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            location = Location.objects.get(pk=pk, user=request.user)
            # Reset all default locations for this user
            Location.objects.filter(user=request.user, is_default=True).update(is_default=False)
            # Set the selected location as default
            location.is_default = True
            location.save()
            return Response({"message": "Default location updated successfully"}, status=status.HTTP_200_OK)
        except Location.DoesNotExist:
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

class UpdateCurrentLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        data = request.data
        user = request.user
        
        try:
            user_location = UserLocation.objects.get(user=user)
            serializer = UserLocationSerializer(user_location, data=data)
        except UserLocation.DoesNotExist:
            serializer = UserLocationSerializer(data=data)
        
        if serializer.is_valid():
            if not hasattr(serializer, 'instance') or serializer.instance is None:
                serializer.save(user=user)
            else:
                serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetCurrentLocationView(generics.RetrieveAPIView):
    serializer_class = UserLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Check if user_id query parameter is provided (for fetching other users' locations)
        user_id = self.request.query_params.get('user_id')
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
                # Only allow if requesting user is handler/admin, or requesting their own location
                if self.request.user.user_type in ['handler', 'admin'] or target_user == self.request.user:
                    return UserLocation.objects.get(user=target_user)
                else:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("You don't have permission to view this user's location")
            except User.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound("User not found")
            except UserLocation.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound("Current location not set for this user")
        else:
            # Get current user's location
            try:
                return UserLocation.objects.get(user=self.request.user)
            except UserLocation.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound("Current location not set")

class AllUsersLocationsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHandler|IsAdmin]
    
    def get(self, request):
        # Get current locations of all users, assistants, or handlers based on query params
        user_type = request.query_params.get('user_type', None)
        order_id = request.query_params.get('order_id', None)
        
        users = User.objects.all()
        if user_type:
            users = users.filter(user_type=user_type)
        
        # If order_id is provided, filter users related to that order
        if order_id:
            from orders.models import Order
            try:
                order = Order.objects.get(id=order_id)
                user_ids = []
                if order.client:
                    user_ids.append(order.client.id)
                if order.assistant:
                    user_ids.append(order.assistant.id)
                if order.handler:
                    user_ids.append(order.handler.id)
                users = users.filter(id__in=user_ids)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        locations = []
        for user in users:
            try:
                location = UserLocation.objects.get(user=user)
                locations.append(location.to_dict())
            except UserLocation.DoesNotExist:
                pass
        
        return Response(locations, status=status.HTTP_200_OK)

class WaypointViewSet(viewsets.ModelViewSet):
    serializer_class = WaypointSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        order_id = self.request.query_params.get('order_id', None)
        
        queryset = Waypoint.objects.all()
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        # Filter based on user type and relationship to orders
        if user.user_type == 'user':  # Client
            from orders.models import Order
            client_orders = Order.objects.filter(client=user).values_list('id', flat=True)
            queryset = queryset.filter(order_id__in=client_orders)
        elif user.user_type == 'assistant':  # Assistant
            from orders.models import Order
            assistant_orders = Order.objects.filter(assistant=user).values_list('id', flat=True)
            queryset = queryset.filter(order_id__in=assistant_orders)
        elif user.user_type in ['handler', 'admin']:
            # Handlers and admins can see all waypoints
            pass
        else:
            queryset = Waypoint.objects.none()
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_visited(self, request, pk=None):
        waypoint = self.get_object()
        waypoint.mark_as_visited()
        return Response({"message": f"Waypoint {waypoint.name} marked as visited"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def for_order(self, request):
        order_id = request.query_params.get('order_id', None)
        if not order_id:
            return Response({"error": "order_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        waypoints = self.get_queryset().filter(order_id=order_id).order_by('order_index')
        serializer = self.get_serializer(waypoints, many=True)
        return Response(serializer.data)

class RouteCalculationViewSet(viewsets.ModelViewSet):
    serializer_class = RouteCalculationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        order_id = self.request.query_params.get('order_id', None)
        
        queryset = RouteCalculation.objects.all()
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        # Filter based on user type and relationship to orders
        if user.user_type == 'user':  # Client
            from orders.models import Order
            client_orders = Order.objects.filter(client=user).values_list('id', flat=True)
            queryset = queryset.filter(order_id__in=client_orders)
        elif user.user_type == 'assistant':  # Assistant
            from orders.models import Order
            assistant_orders = Order.objects.filter(assistant=user).values_list('id', flat=True)
            queryset = queryset.filter(order_id__in=assistant_orders)
        elif user.user_type in ['handler', 'admin']:
            # Handlers and admins can see all routes
            pass
        else:
            queryset = RouteCalculation.objects.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def for_order(self, request):
        order_id = request.query_params.get('order_id', None)
        if not order_id:
            return Response({"error": "order_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        routes = self.get_queryset().filter(order_id=order_id)
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)

class DistanceCalculationView(APIView):
    """
    Calculate distance between two points using OpenStreetMap's OSRM service for accuracy
    Falls back to Haversine formula if OSRM service is not available
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Get coordinates from request
        start_lat = request.data.get('start_lat')
        start_lng = request.data.get('start_lng')
        end_lat = request.data.get('end_lat')
        end_lng = request.data.get('end_lng')
        use_osrm = request.data.get('use_osrm', True)
        order_id = request.data.get('order_id')
        
        # Validate input
        if None in [start_lat, start_lng, end_lat, end_lng]:
            return Response(
                {"error": "Missing coordinates. Please provide start_lat, start_lng, end_lat, and end_lng."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert to float - handle potential string values
            try:
                start_lat = float(start_lat)
                start_lng = float(start_lng)
                end_lat = float(end_lat)
                end_lng = float(end_lng)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid coordinates. Please provide valid numeric values."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate coordinate ranges
            if not (-90 <= start_lat <= 90) or not (-90 <= end_lat <= 90) or \
               not (-180 <= start_lng <= 180) or not (-180 <= end_lng <= 180):
                return Response(
                    {"error": "Coordinates out of range. Latitude must be between -90 and 90, longitude between -180 and 180."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if the coordinates are the same (or very close)
            if abs(start_lat - end_lat) < 0.0001 and abs(start_lng - end_lng) < 0.0001:
                return Response({
                    "distance": 0.0,  # Distance in kilometers
                    "duration": 0.0,  # Duration in minutes
                    "method": "direct",
                    "units": {
                        "distance": "kilometers",
                        "duration": "minutes"
                    }
                })
            
            # Try to use OpenStreetMap's OSRM service for more accurate distance calculation
            if use_osrm:
                try:
                    # Log the attempt to use OSRM
                    print(f"Attempting to use OSRM for distance calculation: {start_lat},{start_lng} to {end_lat},{end_lng}")
                    
                    # Construct the OSRM API URL for route calculation
                    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
                    params = {
                        "overview": "false",  # We don't need the route geometry
                        "alternatives": "false",  # We only need the best route
                        "steps": "false",  # We don't need turn-by-turn instructions
                        "annotations": "false"  # We don't need detailed annotations
                    }
                    
                    # Make the API request with a timeout
                    response = requests.get(osrm_url, params=params, timeout=5)
                    data = response.json()
                    
                    # Check if the API request was successful
                    if response.status_code == 200 and data.get('code') == 'Ok':
                        # Extract distance and duration from the response
                        route = data.get('routes', [{}])[0]
                        
                        # Get distance in meters and convert to kilometers
                        distance_meters = route.get('distance', 0)
                        distance_km = distance_meters / 1000
                        
                        # Get duration in seconds
                        duration_seconds = route.get('duration', 0)
                        duration_minutes = duration_seconds / 60
                        
                        # Ensure we have reasonable values
                        if distance_km > 0:
                            return Response({
                                "distance": round(distance_km, 2),  # Distance in kilometers
                                "duration": round(duration_minutes, 0),  # Duration in minutes
                                "method": "osrm",
                                "units": {
                                    "distance": "kilometers",
                                    "duration": "minutes"
                                }
                            })
                        else:
                            print(f"OSRM returned zero or negative distance: {distance_km}")
                    else:
                        print(f"OSRM API error: {data.get('code')} - {data.get('message', 'No message')}")
                
                except Exception as e:
                    # Log the error and fall back to Haversine formula
                    import traceback
                    print(f"Error using OSRM: {str(e)}")
                    print(traceback.format_exc())
            
            # Fall back to Haversine formula if OSRM is not available or fails
            print(f"Using Haversine formula for distance calculation: {start_lat},{start_lng} to {end_lat},{end_lng}")
            
            # Calculate distance using Haversine formula
            R = 6371  # Earth radius in kilometers
            
            # Convert latitude and longitude from degrees to radians
            lat1_rad = math.radians(start_lat)
            lon1_rad = math.radians(start_lng)
            lat2_rad = math.radians(end_lat)
            lon2_rad = math.radians(end_lng)
            
            # Haversine formula
            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c  # Distance in kilometers
            
            # Add a small factor to account for road routes being longer than straight lines
            # This makes the Haversine calculation more realistic
            distance = distance * 1.2  # Add 20% to approximate road distance
            
            # Calculate approximate duration (assuming average speed of 30 km/h in urban areas)
            duration_hours = distance / 30
            duration_minutes = duration_hours * 60
            
            return Response({
                "distance": round(distance, 2),  # Distance in kilometers
                "duration": round(duration_minutes, 0),  # Duration in minutes
                "method": "haversine",
                "units": {
                    "distance": "kilometers",
                    "duration": "minutes"
                }
            })
            
        except Exception as e:
            # Catch all exceptions to ensure the API doesn't crash
            import traceback
            print(f"Error calculating distance: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"error": "An error occurred while calculating the distance. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except ValueError:
            return Response(
                {"error": "Invalid coordinates. Please provide valid numeric values."},
                status=status.HTTP_400_BAD_REQUEST
            )