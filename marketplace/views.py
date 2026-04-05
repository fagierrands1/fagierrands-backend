from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from datetime import datetime
import uuid

from .models import (
    Vendor, Product, ProductReview, VendorReview,
    Cart, CartItem, MarketplaceOrder, MarketplaceOrderItem
)
from .serializers import (
    VendorListSerializer, VendorDetailSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductReviewSerializer, VendorReviewSerializer,
    CartSerializer, CartItemSerializer,
    MarketplaceOrderSerializer, MarketplaceOrderItemSerializer
)


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.filter(status='active')
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['shop_name', 'city']
    ordering_fields = ['average_rating', 'total_sales', 'created_at']
    ordering = ['-average_rating']
    filterset_fields = ['city', 'is_verified']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VendorDetailSerializer
        return VendorListSerializer
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        vendor = self.get_object()
        products = vendor.products.filter(status='active')
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        vendor = self.get_object()
        reviews = vendor.reviews.all()
        serializer = VendorReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_vendor(self, request):
        try:
            vendor = Vendor.objects.get(user=request.user)
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        except Vendor.DoesNotExist:
            return Response(
                {'error': 'You are not a vendor'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def become_vendor(self, request):
        if hasattr(request.user, 'vendor_profile'):
            return Response(
                {'error': 'You are already a vendor'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = VendorListSerializer(data=request.data)
        if serializer.is_valid():
            vendor = Vendor.objects.create(
                user=request.user,
                **serializer.validated_data
            )
            return Response(
                VendorDetailSerializer(vendor).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(status='active')
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['price', 'average_rating', 'total_sold', 'created_at']
    ordering = ['-created_at']
    filterset_fields = ['category', 'vendor', 'price']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        product = self.get_object()
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not rating or rating not in range(1, 6):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review, created = ProductReview.objects.get_or_create(
            product=product,
            reviewer=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        
        if not created:
            review.rating = rating
            review.comment = comment
            review.save()
        
        self._update_product_rating(product)
        
        serializer = ProductReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.reviews.all()
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def _update_product_rating(product):
        avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg_rating:
            product.average_rating = avg_rating
            product.total_reviews = product.reviews.count()
            product.save()


class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProductReview.objects.filter(reviewer=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class VendorReviewViewSet(viewsets.ModelViewSet):
    serializer_class = VendorReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return VendorReview.objects.filter(reviewer=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id, status='active')
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if quantity > product.quantity_available:
            return Response(
                {'error': 'Insufficient stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.quantity_available:
                return Response(
                    {'error': 'Insufficient stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.save()
        
        cart.save()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data.get('item_id')
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cart.save()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        cart.save()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class MarketplaceOrderViewSet(viewsets.ModelViewSet):
    serializer_class = MarketplaceOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    filterset_fields = ['status', 'payment_status']
    
    def get_queryset(self):
        return MarketplaceOrder.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shipping_address = request.data.get('shipping_address')
        shipping_phone = request.data.get('shipping_phone')
        
        if not shipping_address or not shipping_phone:
            return Response(
                {'error': 'Shipping address and phone are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order_number = f"MPO-{uuid.uuid4().hex[:8].upper()}"
        total_amount = cart.get_total()
        
        order = MarketplaceOrder.objects.create(
            user=request.user,
            order_number=order_number,
            total_amount=total_amount,
            shipping_address=shipping_address,
            shipping_phone=shipping_phone,
            status='pending',
            payment_status='pending'
        )
        
        for item in cart.items.all():
            MarketplaceOrderItem.objects.create(
                order=order,
                product=item.product,
                vendor=item.product.vendor,
                quantity=item.quantity,
                price_at_purchase=item.product.discounted_price or item.product.price
            )
            
            item.product.total_sold += item.quantity
            item.product.quantity_available -= item.quantity
            item.product.save()
        
        cart.items.all().delete()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending':
            return Response(
                {'error': 'Order cannot be confirmed in its current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'confirmed'
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in ['delivered', 'returned', 'cancelled']:
            return Response(
                {'error': 'Order cannot be cancelled in its current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for item in order.items.all():
            if item.product:
                item.product.quantity_available += item.quantity
                item.product.total_sold -= item.quantity
                item.product.save()
        
        order.status = 'cancelled'
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        order = self.get_object()
        order.status = 'delivered'
        order.payment_status = 'completed'
        order.delivered_at = datetime.now()
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
