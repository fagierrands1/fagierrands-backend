from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class DailyMetrics(models.Model):
    """
    Daily app metrics for tracking growth and performance
    """
    date = models.DateField(unique=True)
    
    # User metrics
    total_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)  # Users who logged in that day
    
    # Order metrics
    total_orders = models.IntegerField(default=0)
    new_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ad_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Performance metrics
    avg_order_completion_time = models.DurationField(null=True, blank=True)
    avg_response_time = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Daily Metric'
        verbose_name_plural = 'Daily Metrics'
    
    def __str__(self):
        return f"Metrics for {self.date}"


class CustomerSatisfaction(models.Model):
    """
    Customer satisfaction metrics based on reviews and feedback
    """
    date = models.DateField()
    
    # NPS (Net Promoter Score) categories
    promoters = models.IntegerField(default=0)  # Users who rated 9-10
    passives = models.IntegerField(default=0)   # Users who rated 7-8
    detractors = models.IntegerField(default=0) # Users who rated 0-6
    
    # Calculated NPS score
    nps_score = models.IntegerField(default=0)
    
    # Average ratings
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.IntegerField(default=0)
    
    # Feedback categories
    positive_feedback = models.IntegerField(default=0)
    negative_feedback = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f"Customer Satisfaction for {self.date}"
    
    def calculate_nps(self):
        total = self.promoters + self.passives + self.detractors
        if total > 0:
            self.nps_score = int(((self.promoters - self.detractors) / total) * 100)
        return self.nps_score


class UserRetention(models.Model):
    """
    User retention metrics by cohort
    """
    cohort_date = models.DateField()  # The month users signed up
    
    # Retention by week
    week_1_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    week_2_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    week_4_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Retention by month
    month_1_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    month_2_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    month_3_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    month_6_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Cohort size
    cohort_size = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-cohort_date']
        unique_together = ['cohort_date']
    
    def __str__(self):
        return f"User Retention for cohort {self.cohort_date}"


class ServicePerformance(models.Model):
    """
    Performance metrics for different service types
    """
    SERVICE_TYPES = (
        ('shopping', 'Shopping'),
        ('pickup_delivery', 'Pickup & Delivery'),
        ('cargo_delivery', 'Cargo Delivery'),
        ('handyman', 'Handyman'),
        ('banking', 'Banking'),
    )
    
    date = models.DateField()
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    
    # Order metrics
    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Performance metrics
    avg_completion_time = models.DurationField(null=True, blank=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', 'service_type']
        unique_together = ['date', 'service_type']
    
    def __str__(self):
        return f"{self.get_service_type_display()} Performance for {self.date}"


class AdvertisementMetrics(models.Model):
    """
    Metrics for advertisement performance
    """
    date = models.DateField()
    
    # Impressions and clicks
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    
    # Revenue
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Calculated metrics
    ctr = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Click-through rate
    cpm = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # Cost per mille (1000 impressions)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f"Ad Metrics for {self.date}"
    
    def calculate_ctr(self):
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
        return self.ctr
    
    def calculate_cpm(self):
        if self.impressions > 0:
            self.cpm = (self.revenue / self.impressions) * 1000
        return self.cpm
