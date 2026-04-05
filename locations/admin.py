from django.contrib import admin
from .models import Location, UserLocation

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'address', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('user__username', 'name', 'address')
    date_hierarchy = 'created_at'

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'last_updated')
    search_fields = ('user__username',)
    date_hierarchy = 'last_updated'