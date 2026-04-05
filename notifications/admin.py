from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Notification, PushToken, BroadcastNotification
from .broadcast_service import BroadcastService

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'read', 'created_at')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'token_preview', 'created_at', 'updated_at')
    list_filter = ('device_type', 'created_at')
    search_fields = ('user__username', 'token')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    def token_preview(self, obj):
        """Show first 50 characters of token"""
        return obj.token[:50] + '...' if len(obj.token) > 50 else obj.token
    token_preview.short_description = 'Token'

@admin.register(BroadcastNotification)
class BroadcastNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'notification_type', 
        'target_audience', 
        'status_badge',
        'total_recipients',
        'successful_sends',
        'failed_sends',
        'created_at',
        'action_buttons'
    )
    list_filter = ('notification_type', 'target_audience', 'status', 'created_at')
    search_fields = ('title', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'created_at', 
        'sent_at', 
        'total_recipients', 
        'successful_sends', 
        'failed_sends',
        'status'
    )
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('Targeting', {
            'fields': ('target_audience',)
        }),
        ('Optional Settings', {
            'fields': ('action_url', 'image_url', 'scheduled_for'),
            'classes': ('collapse',)
        }),
        ('Status & Tracking', {
            'fields': (
                'status',
                'total_recipients',
                'successful_sends',
                'failed_sends',
                'created_by',
                'created_at',
                'sent_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'draft': 'gray',
            'scheduled': 'blue',
            'sending': 'orange',
            'sent': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def action_buttons(self, obj):
        """Display action buttons"""
        if obj.status == 'draft':
            return format_html(
                '<a class="button" href="{}">Send Now</a>',
                f'/admin/notifications/broadcastnotification/{obj.id}/send/'
            )
        elif obj.status == 'sent':
            return format_html(
                '<span style="color: green;">✓ Sent</span>'
            )
        elif obj.status == 'failed':
            return format_html(
                '<a class="button" href="{}">Retry</a>',
                f'/admin/notifications/broadcastnotification/{obj.id}/send/'
            )
        return '-'
    action_buttons.short_description = 'Actions'
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        """Add custom URLs for sending broadcasts"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:broadcast_id>/send/',
                self.admin_site.admin_view(self.send_broadcast_view),
                name='notifications_broadcastnotification_send'
            ),
        ]
        return custom_urls + urls
    
    def send_broadcast_view(self, request, broadcast_id):
        """View to send a broadcast notification"""
        try:
            broadcast = BroadcastNotification.objects.get(id=broadcast_id)
            
            if request.method == 'POST':
                # Send the broadcast
                result = BroadcastService.send_broadcast(broadcast_id)
                
                if result['success']:
                    messages.success(
                        request,
                        f'Broadcast sent successfully! '
                        f'{result["successful_sends"]} sent, '
                        f'{result["failed_sends"]} failed.'
                    )
                else:
                    messages.error(
                        request,
                        f'Failed to send broadcast: {result.get("error", "Unknown error")}'
                    )
                
                return redirect('admin:notifications_broadcastnotification_changelist')
            
            # Show confirmation page
            context = {
                'broadcast': broadcast,
                'target_users_count': BroadcastService.get_target_users(
                    broadcast.target_audience
                ).count(),
                'opts': self.model._meta,
                'has_permission': True,
            }
            
            return render(
                request,
                'admin/notifications/send_broadcast_confirm.html',
                context
            )
            
        except BroadcastNotification.DoesNotExist:
            messages.error(request, 'Broadcast notification not found')
            return redirect('admin:notifications_broadcastnotification_changelist')
