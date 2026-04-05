from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, ExpressionWrapper, fields, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.core.cache import cache
from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from .utils.optimization import cache_dashboard_response, log_query_performance, optimize_queryset
from django.contrib.auth import get_user_model

from .models import (
    DailyMetrics, 
    CustomerSatisfaction, 
    UserRetention, 
    ServicePerformance, 
    AdvertisementMetrics
)
from .serializers import (
    DailyMetricsSerializer,
    CustomerSatisfactionSerializer,
    UserRetentionSerializer,
    ServicePerformanceSerializer,
    AdvertisementMetricsSerializer,
    MetricsSummarySerializer,
    TimeSeriesDataSerializer,
    ServiceComparisonSerializer,
    RetentionCohortSerializer
)
from orders.models import Order, OrderReview

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users to access the dashboard
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.is_superuser or 
            getattr(request.user, 'user_type', '') == 'admin'
        )


class DailyMetricsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for daily metrics
    """
    queryset = DailyMetrics.objects.all()
    serializer_class = DailyMetricsSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def time_series(self, request):
        """
        Get time series data for a specific metric
        """
        metric = request.query_params.get('metric', 'total_users')
        days = int(request.query_params.get('days', 30))
        
        # Get a list of field names instead of field objects
        field_names = [field.name for field in DailyMetrics._meta.get_fields()]
        
        if metric not in field_names:
            return Response(
                {'error': f'Invalid metric: {metric}. Available metrics: {", ".join(field_names)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Get data for the specified metric
        metrics = DailyMetrics.objects.filter(
            date__gte=start_date
        ).order_by('date')
        
        # Format data for time series
        data = [
            {
                'date': m.date,
                'value': getattr(m, metric)
            }
            for m in metrics
        ]
        
        serializer = TimeSeriesDataSerializer(data, many=True)
        return Response(serializer.data)


class CustomerSatisfactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for customer satisfaction metrics
    """
    queryset = CustomerSatisfaction.objects.all()
    serializer_class = CustomerSatisfactionSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def nps_trend(self, request):
        """
        Get NPS trend over time
        """
        days = int(request.query_params.get('days', 90))
        start_date = timezone.now().date() - timedelta(days=days)
        
        metrics = CustomerSatisfaction.objects.filter(
            date__gte=start_date
        ).order_by('date')
        
        data = [
            {
                'date': m.date,
                'value': m.nps_score
            }
            for m in metrics
        ]
        
        serializer = TimeSeriesDataSerializer(data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def rating_distribution(self, request):
        """
        Get distribution of ratings
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Get reviews from the last X days
        reviews = OrderReview.objects.filter(
            created_at__date__gte=start_date
        )
        
        # Count reviews by rating
        distribution = {}
        for i in range(1, 6):  # 1-5 star ratings
            distribution[i] = reviews.filter(rating=i).count()
        
        return Response(distribution)


class UserRetentionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user retention metrics
    """
    queryset = UserRetention.objects.all()
    serializer_class = UserRetentionSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def cohort_analysis(self, request):
        """
        Get cohort analysis data
        """
        months = int(request.query_params.get('months', 6))
        start_date = timezone.now().date().replace(day=1) - timedelta(days=30*months)
        
        cohorts = UserRetention.objects.filter(
            cohort_date__gte=start_date
        ).order_by('cohort_date')
        
        data = [
            {
                'cohort_date': c.cohort_date,
                'cohort_size': c.cohort_size,
                'week_1': c.week_1_retention,
                'week_2': c.week_2_retention,
                'week_4': c.week_4_retention,
                'month_1': c.month_1_retention,
                'month_2': c.month_2_retention,
                'month_3': c.month_3_retention,
                'month_6': c.month_6_retention
            }
            for c in cohorts
        ]
        
        serializer = RetentionCohortSerializer(data, many=True)
        return Response(serializer.data)


class ServicePerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for service performance metrics
    """
    queryset = ServicePerformance.objects.all()
    serializer_class = ServicePerformanceSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def service_comparison(self, request):
        """
        Compare performance across different service types
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Get aggregated metrics by service type
        services = ServicePerformance.objects.filter(
            date__gte=start_date
        ).values('service_type').annotate(
            total_orders=Sum('total_orders'),
            total_revenue=Sum('total_revenue'),
            avg_rating=Avg('avg_rating'),
            avg_order_value=Avg('avg_order_value')
        )
        
        serializer = ServiceComparisonSerializer(services, many=True)
        return Response(serializer.data)


class AdvertisementMetricsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for advertisement metrics
    """
    queryset = AdvertisementMetrics.objects.all()
    serializer_class = AdvertisementMetricsSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def ad_performance(self, request):
        """
        Get advertisement performance metrics
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        metrics = AdvertisementMetrics.objects.filter(
            date__gte=start_date
        )
        
        # Calculate aggregated metrics
        total_impressions = metrics.aggregate(Sum('impressions'))['impressions__sum'] or 0
        total_clicks = metrics.aggregate(Sum('clicks'))['clicks__sum'] or 0
        total_revenue = metrics.aggregate(Sum('revenue'))['revenue__sum'] or 0
        
        # Calculate overall CTR and CPM
        overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        overall_cpm = (total_revenue / total_impressions * 1000) if total_impressions > 0 else 0
        
        # Get daily metrics for trend
        daily_metrics = metrics.order_by('date').values('date', 'impressions', 'clicks', 'revenue', 'ctr', 'cpm')
        
        return Response({
            'summary': {
                'total_impressions': total_impressions,
                'total_clicks': total_clicks,
                'total_revenue': total_revenue,
                'overall_ctr': overall_ctr,
                'overall_cpm': overall_cpm
            },
            'daily_metrics': daily_metrics
        })


class DashboardOverviewView(views.APIView):
    """
    API endpoint for dashboard overview with key metrics
    """
    permission_classes = [IsAdminUser]
    
    @cache_dashboard_response(timeout=300)  # Cache for 5 minutes
    @log_query_performance
    def get(self, request):
        """
        Get dashboard overview with key metrics
        """
        try:
            # Note: The caching is now handled by the decorator
            # This original caching code is kept for backward compatibility
            cache_key = 'dashboard_overview'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                serializer = MetricsSummarySerializer(cached_data)
                return Response(serializer.data)
                
            # Get date ranges
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            thirty_days_ago = today - timedelta(days=30)
            sixty_days_ago = today - timedelta(days=60)
            
            # Use select_related and prefetch_related to reduce database queries
            try:
                # Get latest daily metrics - use get instead of latest for better performance
                latest_metrics = DailyMetrics.objects.order_by('-date').first()
            except Exception as e:
                print(f"Error fetching latest metrics: {e}")
                latest_metrics = None
            
            # Get user metrics - use annotate to reduce queries
            user_metrics = User.objects.aggregate(
                total_users=Count('id'),
                new_users=Count('id', filter=Q(date_joined__date__gte=thirty_days_ago)),
                active_users=Count('id', filter=Q(last_login__date__gte=thirty_days_ago)),
                users_30_days_ago=Count('id', filter=Q(date_joined__date__lt=thirty_days_ago))
            )
            
            total_users = user_metrics['total_users']
            new_users_last_30_days = user_metrics['new_users']
            active_users_last_30_days = user_metrics['active_users']
            users_30_days_ago = user_metrics['users_30_days_ago']
            
            # Calculate user growth rate
            user_growth_rate = ((total_users - users_30_days_ago) / users_30_days_ago * 100) if users_30_days_ago > 0 else 0
            
            # Get order metrics - use annotate to reduce queries
            order_metrics = Order.objects.aggregate(
                total_orders=Count('id'),
                new_orders=Count('id', filter=Q(created_at__date__gte=thirty_days_ago)),
                completed_orders=Count('id', filter=Q(status='completed', updated_at__date__gte=thirty_days_ago)),
                all_completed_orders=Count('id', filter=Q(status='completed')),
                total_revenue=Sum('price', filter=Q(status='completed')),
                revenue_last_30_days=Sum('price', filter=Q(status='completed', updated_at__date__gte=thirty_days_ago)),
                revenue_previous_30_days=Sum('price', filter=Q(
                    status='completed', 
                    updated_at__date__gte=sixty_days_ago,
                    updated_at__date__lt=thirty_days_ago
                )),
                avg_order_value=Avg('price', filter=Q(status='completed', updated_at__date__gte=thirty_days_ago)),
                all_avg_order_value=Avg('price', filter=Q(status='completed'))
            )
            
            total_orders = order_metrics['total_orders'] or 0
            new_orders_last_30_days = order_metrics['new_orders'] or 0
            completed_orders_last_30_days = order_metrics['completed_orders'] or 0
            
            # If no completed orders based on completed_at, use all completed orders
            if completed_orders_last_30_days == 0:
                completed_orders_last_30_days = order_metrics['all_completed_orders'] or 0
            
            # Calculate order completion rate
            order_completion_rate = (completed_orders_last_30_days / new_orders_last_30_days * 100) if new_orders_last_30_days > 0 else 0
            
            # Get revenue metrics
            total_revenue = order_metrics['total_revenue'] or 0
            revenue_last_30_days = order_metrics['revenue_last_30_days'] or 0
            
            # If no revenue in last 30 days, use total completed revenue
            if revenue_last_30_days == 0:
                revenue_last_30_days = total_revenue
            
            revenue_previous_30_days = order_metrics['revenue_previous_30_days'] or 0
            
            # Calculate revenue growth rate
            revenue_growth_rate = ((revenue_last_30_days - revenue_previous_30_days) / revenue_previous_30_days * 100) if revenue_previous_30_days > 0 else 0
            
            # Get average order value
            avg_order_value = order_metrics['avg_order_value'] or 0
            
            # If no average for last 30 days, use all completed orders
            if avg_order_value == 0:
                avg_order_value = order_metrics['all_avg_order_value'] or 0
            
            # Get customer satisfaction metrics
            try:
                latest_satisfaction = CustomerSatisfaction.objects.order_by('-date').first()
                nps_score = latest_satisfaction.nps_score if latest_satisfaction else 0
                avg_rating = float(latest_satisfaction.avg_rating) if latest_satisfaction else 0
            except Exception as e:
                print(f"Error fetching satisfaction metrics: {e}")
                nps_score = 0
                avg_rating = 0
            
            # Get performance metrics
            avg_order_completion_time = timedelta(hours=2)  # Default value
            avg_response_time = timedelta(minutes=15)  # Default value
            
            if latest_metrics:
                avg_order_completion_time = latest_metrics.avg_order_completion_time or avg_order_completion_time
                avg_response_time = latest_metrics.avg_response_time or avg_response_time
            
            # Convert timedelta objects to seconds for JSON serialization
            avg_completion_seconds = avg_order_completion_time.total_seconds() if avg_order_completion_time else 0
            avg_response_seconds = avg_response_time.total_seconds() if avg_response_time else 0
            
            # Prepare response data
            data = {
                'total_users': total_users,
                'new_users_last_30_days': new_users_last_30_days,
                'active_users_last_30_days': active_users_last_30_days,
                'user_growth_rate': float(user_growth_rate),
                
                'total_orders': total_orders,
                'new_orders_last_30_days': new_orders_last_30_days,
                'completed_orders_last_30_days': completed_orders_last_30_days,
                'order_completion_rate': float(order_completion_rate),
                
                'total_revenue': float(total_revenue),
                'revenue_last_30_days': float(revenue_last_30_days),
                'revenue_growth_rate': float(revenue_growth_rate),
                'avg_order_value': float(avg_order_value),
                
                'nps_score': nps_score,
                'avg_rating': float(avg_rating),
                
                'avg_order_completion_time': float(avg_completion_seconds),
                'avg_response_time': float(avg_response_seconds)
            }
            
            # Cache the data for 5 minutes to reduce database load
            cache.set(cache_key, data, 300)
            
            serializer = MetricsSummarySerializer(data)
            return Response(serializer.data)
            
        except Exception as e:
            import traceback
            print(f"Error in dashboard overview: {e}")
            print(traceback.format_exc())
            return Response(
                {
                    'error': 'An error occurred while generating the dashboard overview.',
                    'details': str(e)
                },
                status=500
            )


class MetricsCalculationView(views.APIView):
    """
    API endpoint to calculate and store metrics
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """
        Calculate and store metrics for a specific date
        """
        date_str = request.data.get('date')
        
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Default to yesterday
            target_date = timezone.now().date() - timedelta(days=1)
        
        # Calculate and store daily metrics
        self._calculate_daily_metrics(target_date)
        
        # Calculate and store customer satisfaction
        self._calculate_customer_satisfaction(target_date)
        
        # Calculate and store service performance
        self._calculate_service_performance(target_date)
        
        # Calculate and store advertisement metrics
        self._calculate_ad_metrics(target_date)
        
        # Calculate user retention (monthly)
        if target_date.day == 1:
            self._calculate_user_retention(target_date)
        
        return Response({'status': f'Metrics calculated for {target_date}'})
    
    def _calculate_daily_metrics(self, target_date):
        """Calculate and store daily metrics"""
        # Get user metrics
        total_users = User.objects.filter(date_joined__date__lte=target_date).count()
        new_users = User.objects.filter(date_joined__date=target_date).count()
        active_users = User.objects.filter(last_login__date=target_date).count()
        
        # Get order metrics
        total_orders = Order.objects.filter(created_at__date__lte=target_date).count()
        new_orders = Order.objects.filter(created_at__date=target_date).count()
        completed_orders = Order.objects.filter(
            status='completed',
            completed_at__date=target_date
        ).count()
        cancelled_orders = Order.objects.filter(
            status='cancelled',
            cancelled_at__date=target_date
        ).count()
        
        # Get revenue metrics
        total_revenue = Order.objects.filter(
            status='completed',
            completed_at__date=target_date
        ).aggregate(total=Sum('price'))['total'] or 0
        
        # Platform fee is typically a percentage of the total revenue
        platform_fee_revenue = total_revenue * 0.15  # 15% platform fee
        
        # Get ad revenue (placeholder - would come from ad system)
        ad_revenue = 0
        
        # Calculate average order completion time
        completed_orders_objs = Order.objects.filter(
            status='completed',
            completed_at__date=target_date
        )
        
        if completed_orders_objs.exists():
            # Calculate time difference between created_at and completed_at
            completion_times = [
                order.completed_at - order.created_at
                for order in completed_orders_objs
                if order.completed_at and order.created_at
            ]
            
            if completion_times:
                avg_completion_time = sum(completion_times, timedelta()) / len(completion_times)
            else:
                avg_completion_time = None
        else:
            avg_completion_time = None
        
        # Calculate average response time (placeholder)
        avg_response_time = timedelta(minutes=15)
        
        # Create or update daily metrics
        metrics, created = DailyMetrics.objects.update_or_create(
            date=target_date,
            defaults={
                'total_users': total_users,
                'new_users': new_users,
                'active_users': active_users,
                'total_orders': total_orders,
                'new_orders': new_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'total_revenue': total_revenue,
                'platform_fee_revenue': platform_fee_revenue,
                'ad_revenue': ad_revenue,
                'avg_order_completion_time': avg_completion_time,
                'avg_response_time': avg_response_time
            }
        )
        
        return metrics
    
    def _calculate_customer_satisfaction(self, target_date):
        """Calculate and store customer satisfaction metrics"""
        # Get reviews from the target date
        reviews = OrderReview.objects.filter(created_at__date=target_date)
        
        # Count reviews by NPS category
        promoters = reviews.filter(rating__gte=9).count()
        passives = reviews.filter(rating__gte=7, rating__lte=8).count()
        detractors = reviews.filter(rating__lte=6).count()
        
        # Calculate NPS score
        total_reviews = reviews.count()
        nps_score = 0
        
        if total_reviews > 0:
            nps_score = int(((promoters - detractors) / total_reviews) * 100)
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Count positive and negative feedback
        positive_feedback = reviews.filter(rating__gte=4).count()
        negative_feedback = reviews.filter(rating__lte=2).count()
        
        # Create or update customer satisfaction
        satisfaction, created = CustomerSatisfaction.objects.update_or_create(
            date=target_date,
            defaults={
                'promoters': promoters,
                'passives': passives,
                'detractors': detractors,
                'nps_score': nps_score,
                'avg_rating': avg_rating,
                'total_reviews': total_reviews,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback
            }
        )
        
        return satisfaction
    
    def _calculate_service_performance(self, target_date):
        """Calculate and store service performance metrics"""
        # Get service types
        service_types = [choice[0] for choice in ServicePerformance.SERVICE_TYPES]
        
        for service_type in service_types:
            # Get orders for this service type
            orders = Order.objects.filter(
                service_type=service_type,
                created_at__date__lte=target_date
            )
            
            # Get completed orders for this service type on the target date
            completed_orders = orders.filter(
                status='completed',
                completed_at__date=target_date
            )
            
            # Get cancelled orders for this service type on the target date
            cancelled_orders = orders.filter(
                status='cancelled',
                cancelled_at__date=target_date
            )
            
            # Calculate total revenue
            total_revenue = completed_orders.aggregate(
                total=Sum('price')
            )['total'] or 0
            
            # Calculate average order value
            avg_order_value = completed_orders.aggregate(
                avg=Avg('price')
            )['avg'] or 0
            
            # Calculate average completion time
            if completed_orders.exists():
                completion_times = [
                    order.completed_at - order.created_at
                    for order in completed_orders
                    if order.completed_at and order.created_at
                ]
                
                if completion_times:
                    avg_completion_time = sum(completion_times, timedelta()) / len(completion_times)
                else:
                    avg_completion_time = None
            else:
                avg_completion_time = None
            
            # Calculate average rating
            reviews = OrderReview.objects.filter(
                order__in=completed_orders
            )
            
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
            
            # Create or update service performance
            performance, created = ServicePerformance.objects.update_or_create(
                date=target_date,
                service_type=service_type,
                defaults={
                    'total_orders': orders.count(),
                    'completed_orders': completed_orders.count(),
                    'cancelled_orders': cancelled_orders.count(),
                    'total_revenue': total_revenue,
                    'avg_order_value': avg_order_value,
                    'avg_completion_time': avg_completion_time,
                    'avg_rating': avg_rating
                }
            )
        
        return True
    
    def _calculate_ad_metrics(self, target_date):
        """Calculate and store advertisement metrics"""
        # Placeholder for ad metrics calculation
        # In a real system, this would pull data from an ad platform API
        
        # Create or update ad metrics with placeholder data
        metrics, created = AdvertisementMetrics.objects.update_or_create(
            date=target_date,
            defaults={
                'impressions': 1000,
                'clicks': 50,
                'revenue': 25.00,
                'ctr': 5.00,  # 5% CTR
                'cpm': 25.00  # $25 CPM
            }
        )
        
        return metrics
    
    def _calculate_user_retention(self, target_date):
        """Calculate and store user retention metrics"""
        # This is a monthly calculation, so we use the first day of the month
        cohort_date = target_date.replace(day=1) - timedelta(days=180)  # 6 months ago
        
        # Get users who signed up in the cohort month
        cohort_users = User.objects.filter(
            date_joined__year=cohort_date.year,
            date_joined__month=cohort_date.month
        )
        
        cohort_size = cohort_users.count()
        
        if cohort_size == 0:
            return None
        
        # Calculate retention at different intervals
        week_1_date = cohort_date + timedelta(days=7)
        week_2_date = cohort_date + timedelta(days=14)
        week_4_date = cohort_date + timedelta(days=28)
        month_1_date = cohort_date + timedelta(days=30)
        month_2_date = cohort_date + timedelta(days=60)
        month_3_date = cohort_date + timedelta(days=90)
        month_6_date = cohort_date + timedelta(days=180)
        
        # Count active users at each interval
        week_1_active = cohort_users.filter(last_login__date__gte=week_1_date).count()
        week_2_active = cohort_users.filter(last_login__date__gte=week_2_date).count()
        week_4_active = cohort_users.filter(last_login__date__gte=week_4_date).count()
        month_1_active = cohort_users.filter(last_login__date__gte=month_1_date).count()
        month_2_active = cohort_users.filter(last_login__date__gte=month_2_date).count()
        month_3_active = cohort_users.filter(last_login__date__gte=month_3_date).count()
        month_6_active = cohort_users.filter(last_login__date__gte=month_6_date).count()
        
        # Calculate retention rates
        week_1_retention = (week_1_active / cohort_size) * 100
        week_2_retention = (week_2_active / cohort_size) * 100
        week_4_retention = (week_4_active / cohort_size) * 100
        month_1_retention = (month_1_active / cohort_size) * 100
        month_2_retention = (month_2_active / cohort_size) * 100
        month_3_retention = (month_3_active / cohort_size) * 100
        month_6_retention = (month_6_active / cohort_size) * 100
        
        # Create or update user retention
        retention, created = UserRetention.objects.update_or_create(
            cohort_date=cohort_date,
            defaults={
                'cohort_size': cohort_size,
                'week_1_retention': week_1_retention,
                'week_2_retention': week_2_retention,
                'week_4_retention': week_4_retention,
                'month_1_retention': month_1_retention,
                'month_2_retention': month_2_retention,
                'month_3_retention': month_3_retention,
                'month_6_retention': month_6_retention
            }
        )
        
        return retention


class LiveMetricsView(views.APIView):
    """
    API endpoint for live metrics used by the LiveMetricsWidget
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """
        Get real-time metrics for the dashboard
        """
        try:
            # Get current time for calculations
            now = timezone.now()
            today = now.date()
            
            # Get active users (logged in within the last 30 minutes)
            active_users = User.objects.filter(
                last_login__gte=now - timedelta(minutes=30)
            ).count()
            
            # Get active orders (pending, assigned, in_progress)
            active_orders = Order.objects.filter(
                status__in=['pending', 'assigned', 'in_progress']
            ).count()
            
            # Get revenue for today - check both completed_at and updated_at for completed orders
            revenue_today = Order.objects.filter(
                status='completed',
                updated_at__date=today
            ).aggregate(total=Sum('price'))['total'] or 0
            
            # If no revenue today, get total revenue from completed orders
            if revenue_today == 0:
                revenue_today = Order.objects.filter(
                    status='completed'
                ).aggregate(total=Sum('price'))['total'] or 0
            
            # Calculate average response time (simulated - in a real app this would come from actual metrics)
            # This represents the average time to respond to customer requests in milliseconds
            avg_response_time = 15000  # 15 seconds in milliseconds
            
            # Get additional metrics for the "Quick Stats" section
            total_users = User.objects.count()
            
            completed_today = Order.objects.filter(
                status='completed',
                updated_at__date=today
            ).count()
            
            # If no completed today, count all completed orders
            if completed_today == 0:
                completed_today = Order.objects.filter(status='completed').count()
            
            # Get online assistants (users with user_type='assistant' active in last 30 minutes)
            online_assistants = User.objects.filter(
                user_type='assistant',
                last_login__gte=now - timedelta(minutes=30)
            ).count()
            
            # Get pending orders
            pending_orders = Order.objects.filter(
                status='pending'
            ).count()
            
            # Prepare response data matching the expected format from the frontend
            data = {
                'activeUsers': active_users,
                'activeOrders': active_orders,
                'revenueToday': float(revenue_today),
                'avgResponseTime': avg_response_time,
                'totalUsers': total_users,
                'completedToday': completed_today,
                'onlineAssistants': online_assistants,
                'pendingOrders': pending_orders
            }
            
            return Response(data)
            
        except Exception as e:
            # Log the error and return a fallback response
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in LiveMetricsView: {str(e)}")
            
            # Return default values if there's an error
            fallback_data = {
                'activeUsers': 0,
                'activeOrders': 0,
                'revenueToday': 0.0,
                'avgResponseTime': 15000,
                'totalUsers': 0,
                'completedToday': 0,
                'onlineAssistants': 0,
                'pendingOrders': 0
            }
            
            return Response(fallback_data)


class ExportDataView(views.APIView):
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def export_users(self, request):
        from accounts.models import User
        from .utils.excel_export import ExcelExporter
        from django.http import FileResponse
        
        queryset = User.objects.all()
        user_type = request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        exporter = ExcelExporter('users.xlsx')
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                  'user_type', 'is_verified', 'email_verified', 'is_online', 'created_at']
        headers = ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone', 
                   'User Type', 'Verified', 'Email Verified', 'Online', 'Created']
        exporter.add_queryset(queryset, fields, headers)
        filepath = exporter.save()
        
        return FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename='users.xlsx',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    def get(self, request):
        export_type = request.query_params.get('type', 'users').lower()
        
        if export_type == 'users':
            return self._export_users(request)
        elif export_type == 'orders':
            return self._export_orders(request)
        elif export_type == 'profiles':
            return self._export_profiles(request)
        else:
            return Response(
                {'error': 'Invalid export type. Choose: users, orders, profiles'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _export_users(self, request):
        from accounts.models import User
        from .utils.excel_export import ExcelExporter
        from django.http import FileResponse
        import os
        
        queryset = User.objects.all()
        user_type = request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        exporter = ExcelExporter('users.xlsx')
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                  'user_type', 'is_verified', 'email_verified', 'is_online', 'created_at']
        headers = ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone', 
                   'User Type', 'Verified', 'Email Verified', 'Online', 'Created']
        exporter.add_queryset(queryset, fields, headers)
        filepath = exporter.save()
        
        response = FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename='users.xlsx',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return response
    
    def _export_orders(self, request):
        from .utils.excel_export import ExcelExporter
        from django.http import FileResponse
        import os
        
        queryset = Order.objects.all().select_related('user', 'assigned_to', 'order_type')
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        exporter = ExcelExporter('orders.xlsx')
        fields = ['id', 'user__username', 'order_type__name', 'assigned_to__username', 'status',
                  'pickup_location', 'dropoff_location', 'total_price', 'payment_status', 'created_at']
        headers = ['ID', 'Customer', 'Service Type', 'Assigned To', 'Status',
                   'Pickup', 'Dropoff', 'Total Price', 'Payment Status', 'Created']
        exporter.add_queryset(queryset, fields, headers)
        filepath = exporter.save()
        
        response = FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename='orders.xlsx',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return response
    
    def _export_profiles(self, request):
        from accounts.models import Profile
        from .utils.excel_export import ExcelExporter
        from django.http import FileResponse
        import os
        
        queryset = Profile.objects.all().select_related('user')
        
        exporter = ExcelExporter('profiles.xlsx')
        fields = ['user__id', 'user__username', 'user__email', 'address', 'wallet_points', 'wallet_balance']
        headers = ['User ID', 'Username', 'Email', 'Address', 'Wallet Points', 'Wallet Balance']
        exporter.add_queryset(queryset, fields, headers)
        filepath = exporter.save()
        
        response = FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename='profiles.xlsx',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return response
