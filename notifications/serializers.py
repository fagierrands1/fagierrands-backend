from rest_framework import serializers
from .models import Notification, PushToken, UserPushSubscription

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'read', 'created_at', 'content_type', 'object_id']
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'created_at', 'content_type', 'object_id']

class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ['id', 'token', 'device_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Update existing token if it exists
        try:
            token = PushToken.objects.get(
                user=validated_data['user'],
                token=validated_data['token']
            )
            token.device_type = validated_data['device_type']
            token.save()
            return token
        except PushToken.DoesNotExist:
            return super().create(validated_data)

class UserPushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPushSubscription
        fields = ['id', 'subscription_data', 'user_agent', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Update existing subscription if it exists
        try:
            subscription = UserPushSubscription.objects.get(user=validated_data['user'])
            subscription.subscription_data = validated_data['subscription_data']
            subscription.user_agent = validated_data.get('user_agent', '')
            subscription.is_active = True
            subscription.save()
            return subscription
        except UserPushSubscription.DoesNotExist:
            return super().create(validated_data)