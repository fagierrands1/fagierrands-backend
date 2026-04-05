from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocationListCreateView, LocationDetailView, SetDefaultLocationView,
    UpdateCurrentLocationView, GetCurrentLocationView, AllUsersLocationsView,
    WaypointViewSet, RouteCalculationViewSet, DistanceCalculationView
)
from .api import MapConfigView

router = DefaultRouter()
router.register(r'waypoints', WaypointViewSet, basename='waypoint')
router.register(r'routes', RouteCalculationViewSet, basename='route')

urlpatterns = [
    path('', include(router.urls)),
    path('locations/', LocationListCreateView.as_view(), name='location-list-create'),
    path('<int:pk>/', LocationDetailView.as_view(), name='location-detail'),
    path('<int:pk>/set-default/', SetDefaultLocationView.as_view(), name='set-default-location'),
    path('current/', GetCurrentLocationView.as_view(), name='get-current-location'),
    path('current/update/', UpdateCurrentLocationView.as_view(), name='update-current-location'),
    path('all-users/', AllUsersLocationsView.as_view(), name='all-users-locations'),
    path('calculate-distance/', DistanceCalculationView.as_view(), name='calculate-distance'),
    path('map-config/', MapConfigView.as_view(), name='map-config'),
]