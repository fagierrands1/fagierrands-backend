import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import UserLocation, Waypoint
from orders.models import Order

User = get_user_model()

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.order_id = self.scope['url_route']['kwargs'].get('order_id')
        
        # Create a unique group name for this order
        self.room_group_name = f'order_{self.order_id}_location'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial locations when connecting
        if self.order_id:
            locations = await self.get_order_locations(self.order_id)
            await self.send(text_data=json.dumps({
                'type': 'initial_locations',
                'locations': locations
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'update_location':
            # Update user location in database
            await self.update_user_location(
                user_id=self.user.id,
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                heading=data.get('heading'),
                speed=data.get('speed'),
                accuracy=data.get('accuracy')
            )
            
            # Send location update to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'location_update',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'user_type': self.user.user_type,
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'heading': data.get('heading'),
                    'speed': data.get('speed'),
                    'accuracy': data.get('accuracy')
                }
            )
        
        elif message_type == 'waypoint_visited':
            # Mark waypoint as visited
            waypoint_id = data.get('waypoint_id')
            if waypoint_id:
                success = await self.mark_waypoint_visited(waypoint_id)
                
                if success:
                    # Send waypoint update to group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'waypoint_update',
                            'waypoint_id': waypoint_id,
                            'is_visited': True,
                            'user_id': self.user.id,
                            'username': self.user.username
                        }
                    )

    # Receive message from room group
    async def location_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'user_type': event['user_type'],
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'heading': event.get('heading'),
            'speed': event.get('speed'),
            'accuracy': event.get('accuracy')
        }))
    
    # Receive waypoint update from room group
    async def waypoint_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'waypoint_update',
            'waypoint_id': event['waypoint_id'],
            'is_visited': event['is_visited'],
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    @database_sync_to_async
    def update_user_location(self, user_id, latitude, longitude, heading=None, speed=None, accuracy=None):
        user = User.objects.get(id=user_id)
        
        try:
            location = UserLocation.objects.get(user=user)
            location.latitude = latitude
            location.longitude = longitude
            location.heading = heading
            location.speed = speed
            location.accuracy = accuracy
            location.save()
        except UserLocation.DoesNotExist:
            UserLocation.objects.create(
                user=user,
                latitude=latitude,
                longitude=longitude,
                heading=heading,
                speed=speed,
                accuracy=accuracy
            )
        
        return True
    
    @database_sync_to_async
    def mark_waypoint_visited(self, waypoint_id):
        try:
            waypoint = Waypoint.objects.get(id=waypoint_id)
            waypoint.mark_as_visited()
            return True
        except Waypoint.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_order_locations(self, order_id):
        try:
            order = Order.objects.get(id=order_id)
            result = {
                'order': {
                    'id': order.id,
                    'title': order.title,
                    'status': order.status,
                    'distance': order.distance,
                    'estimated_duration': order.estimated_duration
                },
                'users': [],
                'waypoints': []
            }
            
            # Get user locations
            users = []
            if order.client:
                users.append(order.client)
            if order.assistant:
                users.append(order.assistant)
            if order.handler:
                users.append(order.handler)
            
            for user in users:
                try:
                    location = UserLocation.objects.get(user=user)
                    result['users'].append(location.to_dict())
                except UserLocation.DoesNotExist:
                    pass
            
            # Get waypoints
            waypoints = Waypoint.objects.filter(order=order).order_by('order_index')
            result['waypoints'] = [waypoint.to_dict() for waypoint in waypoints]
            
            return result
        except Order.DoesNotExist:
            return {
                'order': None,
                'users': [],
                'waypoints': []
            }