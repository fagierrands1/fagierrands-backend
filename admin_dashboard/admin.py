from django.contrib import admin
from .models import (
    DailyMetrics, 
    CustomerSatisfaction, 
    UserRetention, 
    ServicePerformance, 
    AdvertisementMetrics
)

@admin.register(DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'new_users', 'active_users', 'total_orders', 'new_orders', 'total_revenue')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CustomerSatisfaction)
class CustomerSatisfactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'nps_score', 'avg_rating', 'total_reviews', 'positive_feedback', 'negative_feedback')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserRetention)
class UserRetentionAdmin(admin.ModelAdmin):
    list_display = ('cohort_date', 'cohort_size', 'week_1_retention', 'month_1_retention', 'month_3_retention')
    list_filter = ('cohort_date',)
    date_hierarchy = 'cohort_date'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ServicePerformance)
class ServicePerformanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'service_type', 'total_orders', 'completed_orders', 'total_revenue', 'avg_rating')
    list_filter = ('date', 'service_type')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AdvertisementMetrics)
class AdvertisementMetricsAdmin(admin.ModelAdmin):
    list_display = ('date', 'impressions', 'clicks', 'revenue', 'ctr', 'cpm')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
