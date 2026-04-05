from rest_framework import serializers
from .models import (
    DailyMetrics, 
    CustomerSatisfaction, 
    UserRetention, 
    ServicePerformance, 
    AdvertisementMetrics
)

class DailyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMetrics
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CustomerSatisfactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSatisfaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class UserRetentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRetention
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ServicePerformanceSerializer(serializers.ModelSerializer):
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    
    class Meta:
        model = ServicePerformance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AdvertisementMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvertisementMetrics
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# Summary serializers for dashboard overview
class MetricsSummarySerializer(serializers.Serializer):
    # User metrics
    total_users = serializers.IntegerField()
    new_users_last_30_days = serializers.IntegerField()
    active_users_last_30_days = serializers.IntegerField()
    user_growth_rate = serializers.FloatField()
    
    # Order metrics
    total_orders = serializers.IntegerField()
    new_orders_last_30_days = serializers.IntegerField()
    completed_orders_last_30_days = serializers.IntegerField()
    order_completion_rate = serializers.FloatField()
    
    # Revenue metrics
    total_revenue = serializers.FloatField()  # Changed to FloatField to handle both Decimal and float
    revenue_last_30_days = serializers.FloatField()  # Changed to FloatField to handle both Decimal and float
    revenue_growth_rate = serializers.FloatField()
    avg_order_value = serializers.FloatField()  # Changed to FloatField to handle both Decimal and float
    
    # Customer satisfaction
    nps_score = serializers.IntegerField()
    avg_rating = serializers.FloatField()  # Changed to FloatField to handle both Decimal and float
    
    # Performance metrics
    avg_order_completion_time = serializers.FloatField()  # Changed to FloatField to handle seconds
    avg_response_time = serializers.FloatField()  # Changed to FloatField to handle seconds


class TimeSeriesDataSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = serializers.FloatField()


class ServiceComparisonSerializer(serializers.Serializer):
    service_type = serializers.CharField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=8, decimal_places=2)


class RetentionCohortSerializer(serializers.Serializer):
    cohort_date = serializers.DateField()
    cohort_size = serializers.IntegerField()
    week_1 = serializers.FloatField()
    week_2 = serializers.FloatField()
    week_4 = serializers.FloatField()
    month_1 = serializers.FloatField()
    month_2 = serializers.FloatField()
    month_3 = serializers.FloatField()
    month_6 = serializers.FloatField()
