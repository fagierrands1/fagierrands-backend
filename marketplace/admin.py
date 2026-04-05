from django.contrib import admin
from .models import (
    Vendor, Product, ProductReview, VendorReview,
    Cart, CartItem, MarketplaceOrder, MarketplaceOrderItem
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'user', 'average_rating', 'total_sales', 'status', 'is_verified', 'created_at']
    list_filter = ['status', 'is_verified', 'created_at']
    search_fields = ['shop_name', 'user__username']
    readonly_fields = ['average_rating', 'total_reviews', 'total_sales', 'created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'discounted_price', 'quantity_available', 'average_rating', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'vendor']
    search_fields = ['name', 'description', 'category']
    readonly_fields = ['average_rating', 'total_reviews', 'total_sold', 'created_at', 'updated_at']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'reviewer__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['vendor__shop_name', 'reviewer__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name']


@admin.register(MarketplaceOrder)
class MarketplaceOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__username']
    readonly_fields = ['order_number', 'created_at', 'updated_at']


@admin.register(MarketplaceOrderItem)
class MarketplaceOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'vendor', 'quantity', 'price_at_purchase']
    list_filter = ['order__created_at']
    search_fields = ['product__name', 'order__order_number']
