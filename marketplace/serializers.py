from rest_framework import serializers
from .models import (
    Vendor, Product, ProductReview, VendorReview, 
    Cart, CartItem, MarketplaceOrder, MarketplaceOrderItem
)
from accounts.models import User


class VendorListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'user', 'user_name', 'shop_name', 'shop_description', 
            'shop_image_url', 'average_rating', 'total_reviews', 'total_sales',
            'is_verified', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'average_rating', 'total_reviews', 'total_sales', 'created_at']


class VendorDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'user', 'user_name', 'shop_name', 'shop_description',
            'shop_image_url', 'phone_number', 'city', 'address',
            'average_rating', 'total_reviews', 'total_sales', 'reviews',
            'is_verified', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'average_rating', 'total_reviews', 'total_sales', 'created_at', 'updated_at']
    
    def get_reviews(self, obj):
        reviews = obj.reviews.all()[:5]
        return VendorReviewSerializer(reviews, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_name', 'name', 'category', 'price',
            'discounted_price', 'discount_percentage', 'image_url',
            'average_rating', 'total_reviews', 'total_sold', 'status',
            'quantity_available', 'created_at'
        ]
        read_only_fields = ['id', 'average_rating', 'total_reviews', 'total_sold', 'created_at', 'discount_percentage']


class ProductDetailSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    vendor_id = serializers.IntegerField(source='vendor.id', read_only=True)
    vendor_rating = serializers.DecimalField(source='vendor.average_rating', max_digits=3, decimal_places=2, read_only=True)
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_id', 'vendor_name', 'vendor_rating',
            'name', 'description', 'category', 'price', 'discounted_price',
            'discount_percentage', 'quantity_available', 'image_url',
            'additional_images', 'average_rating', 'total_reviews', 'total_sold',
            'reviews', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'average_rating', 'total_reviews', 'total_sold', 'created_at', 'updated_at', 'discount_percentage']
    
    def get_reviews(self, obj):
        reviews = obj.reviews.all()[:10]
        return ProductReviewSerializer(reviews, many=True).data


class ProductReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'reviewer', 'reviewer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class VendorReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    
    class Meta:
        model = VendorReview
        fields = ['id', 'reviewer', 'reviewer_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.CharField(source='product.image_url', read_only=True)
    price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product_name', 'product_image', 'price', 'quantity', 'subtotal']
    
    def get_price(self, obj):
        return obj.product.discounted_price or obj.product.price
    
    def get_subtotal(self, obj):
        return obj.get_subtotal()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'updated_at']
    
    def get_total(self, obj):
        return obj.get_total()


class MarketplaceOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.CharField(source='product.image_url', read_only=True)
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    
    class Meta:
        model = MarketplaceOrderItem
        fields = [
            'id', 'product_name', 'product_image', 'vendor_name',
            'quantity', 'price_at_purchase', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MarketplaceOrderSerializer(serializers.ModelSerializer):
    items = MarketplaceOrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = MarketplaceOrder
        fields = [
            'id', 'order_number', 'user', 'user_name', 'status',
            'payment_status', 'total_amount', 'delivery_fee',
            'shipping_address', 'shipping_phone', 'items',
            'created_at', 'updated_at', 'delivered_at'
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at', 'delivered_at']
