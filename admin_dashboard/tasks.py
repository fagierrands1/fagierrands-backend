from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def calculate_daily_metrics():
    """
    Celery task to calculate daily metrics for the previous day
    """
    from .views import MetricsCalculationView
    
    try:
        # Calculate metrics for yesterday
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Create a view instance
        view = MetricsCalculationView()
        
        # Calculate metrics
        view._calculate_daily_metrics(yesterday)
        view._calculate_customer_satisfaction(yesterday)
        view._calculate_service_performance(yesterday)
        view._calculate_ad_metrics(yesterday)
        
        # Calculate user retention on the first day of the month
        if yesterday.day == 1:
            view._calculate_user_retention(yesterday)
        
        logger.info(f"Successfully calculated metrics for {yesterday}")
        return f"Metrics calculated for {yesterday}"
    
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        return f"Error calculating metrics: {str(e)}"
        
from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def calculate_daily_metrics():
    """
    Celery task to calculate daily metrics for the previous day
    """
    from .views import MetricsCalculationView
    
    try:
        # Calculate metrics for yesterday
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Create a view instance
        view = MetricsCalculationView()
        
        # Calculate metrics
        view._calculate_daily_metrics(yesterday)
        view._calculate_customer_satisfaction(yesterday)
        view._calculate_service_performance(yesterday)
        view._calculate_ad_metrics(yesterday)
        
        # Calculate user retention on the first day of the month
        if yesterday.day == 1:
            view._calculate_user_retention(yesterday)
        
        logger.info(f"Successfully calculated metrics for {yesterday}")
        return f"Metrics calculated for {yesterday}"
    
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        return f"Error calculating metrics: {str(e)}"