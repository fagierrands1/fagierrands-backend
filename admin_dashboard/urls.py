from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DailyMetricsViewSet,
    CustomerSatisfactionViewSet,
    UserRetentionViewSet,
    ServicePerformanceViewSet,
    AdvertisementMetricsViewSet,
    DashboardOverviewView,
    MetricsCalculationView,
    LiveMetricsView,
    ExportDataView
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'daily-metrics', DailyMetricsViewSet)
router.register(r'customer-satisfaction', CustomerSatisfactionViewSet)
router.register(r'user-retention', UserRetentionViewSet)
router.register(r'service-performance', ServicePerformanceViewSet)
router.register(r'advertisement-metrics', AdvertisementMetricsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('calculate-metrics/', MetricsCalculationView.as_view(), name='calculate-metrics'),
    path('live-metrics/', LiveMetricsView.as_view(), name='live-metrics'),
    path('export/', ExportDataView.as_view(), name='export-data'),
]