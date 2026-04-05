from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VendorViewSet, ProductViewSet, ProductReviewViewSet, VendorReviewViewSet,
    CartViewSet, MarketplaceOrderViewSet
)

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-reviews', ProductReviewViewSet, basename='product-review')
router.register(r'vendor-reviews', VendorReviewViewSet, basename='vendor-review')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', MarketplaceOrderViewSet, basename='marketplace-order')

urlpatterns = [
    path('', include(router.urls)),
]
