from django.urls import path, include
from .views import (
    OrderTypeListView, OrderListCreateView, OrderDetailView,
    OrderStatusUpdateView, AssignOrderView, ShoppingItemListCreateView,
    OrderImageUploadView, OrderReviewCreateView, PendingOrdersView,
    AssistantOrdersView, AvailableOrdersView, AcceptOrderView, ShoppingOrderView, AssistantOrdersAPIView,
    HandymanServiceTypeListView,
    HandymanOrderListCreateView,
    HandymanOrderDetailView,
    HandymanOrderStatusUpdateView,
    AssignHandymanOrderView,
    HandymanOrderImageUploadView,
    PendingHandymanOrdersView,
    AssistantHandymanOrdersView,
    HandymanServiceQuoteView,
    deployment_check_view,
    PickupDeliveryOrderCreateView,
    CargoDeliveryOrderView,
    HandlerAllOrdersView,  # New handler-specific view
    # New views from views_updated.py
    ClientFeedbackCreateView,
    ClientFeedbackDetailView,
    RiderFeedbackCreateView,
    RiderFeedbackDetailView,
    CargoPhotoUploadView,
    CargoValueView,
    ReportIssueCreateView,
    ReportIssueListView,
    ReferralCreateView,
    ReferralListView,
    PriceCalculationView, OrderPriceRealtimeUpdateView,
    GenerateQRView,
)
# Import attachment views
from .attachments_views import AttachmentUploadView, AttachmentListView, AttachmentDetailView
from .views_banking import BankListView, BankingOrderListCreateView, BankingOrderDetailView, BankingOrderCancelView
# Import tracking views
from .views_updated import (
    OrderTrackingView, TrackingWaypointListCreateView, TrackingWaypointDetailView,
    TrackingEventListCreateView, TrackingEventDetailView, TrackingLocationHistoryListView,
    InitializeTrackingView
)
# Import payment views (NCBA Till API)
from .views_payment_ncba import (
    InitiatePaymentView, PaymentStatusView, NCBAPaymentView,
    NCBACallbackView, OrderPaymentStatusView, NCBAQRGenerationView,
    PaymentCancellationView
)
# Import handyman payment view
from .views_handyman_payment import HandymanServiceFinalPaymentView

# Import quote management views
from .views_quotes import (
    ServiceProviderQuoteListView, ServiceProviderQuoteDetailView,
    SubmitQuoteView, HandlerQuoteManagementView, ApproveRejectQuoteView,
    HandymanOrderQuotesView, QuoteImageUploadView, ServiceProviderDashboardView,
    quote_status_check
)

# Import enhanced order views
from .views_enhanced_order import (
    EnhancedPickupDeliveryOrderView,
    PriceCalculationView,
    EnhancedOrderImageUploadView
)

# Import 3-step order views
from .views_three_step_order import (
    CreateDraftOrderView,
    UploadOrderImageView,
    ConfirmOrderView
)

# Import 2-step errand placement views
from .views_errand_placement import (
    calculate_errand_price,
    create_draft_errand,
    upload_errand_image,
    update_errand_receiver_info,
    confirm_errand,
    get_draft_errand,
    delete_draft_errand
)

urlpatterns = [
    # 2-Step Errand Placement (Normal Errands - Pickup & Delivery)
    path('errands/calculate-price/', calculate_errand_price, name='calculate-errand-price'),
    path('errands/draft/', create_draft_errand, name='create-draft-errand'),
    path('errands/<int:order_id>/upload-image/', upload_errand_image, name='upload-errand-image'),
    path('errands/<int:order_id>/receiver-info/', update_errand_receiver_info, name='update-errand-receiver-info'),
    path('errands/<int:order_id>/confirm/', confirm_errand, name='confirm-errand'),
    path('errands/<int:order_id>/', get_draft_errand, name='get-draft-errand'),
    path('errands/<int:order_id>/delete/', delete_draft_errand, name='delete-draft-errand'),
    
    # 3-Step Order Creation (RECOMMENDED)
    path('v1/draft/', CreateDraftOrderView.as_view(), name='create-draft-order'),
    path('v1/<int:order_id>/upload-image/', UploadOrderImageView.as_view(), name='upload-order-image'),
    path('v1/<int:order_id>/confirm/', ConfirmOrderView.as_view(), name='confirm-order'),
    
    # Enhanced order endpoints (NEW - Use these!)
    path('v1/create/', EnhancedPickupDeliveryOrderView.as_view(), name='enhanced-order-create'),
    path('v1/calculate-price/', PriceCalculationView.as_view(), name='calculate-price-v1'),
    
    # Existing order endpoints
    path('types/', OrderTypeListView.as_view(), name='order-type-list'),
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('shopping/', ShoppingOrderView.as_view(), name='shopping-order'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('<int:pk>/assign/', AssignOrderView.as_view(), name='assign-order'),
    path('<int:pk>/accept/', AcceptOrderView.as_view(), name='accept-order'),
    path('<int:order_id>/items/', ShoppingItemListCreateView.as_view(), name='shopping-item-list-create'),
    path('<int:order_id>/images/', OrderImageUploadView.as_view(), name='order-image-upload'),
    path('<int:order_id>/review/', OrderReviewCreateView.as_view(), name='order-review-create'),
    
    # Attachment endpoints
    path('<int:order_id>/attachments/upload/', AttachmentUploadView.as_view(), name='order-attachment-upload'),
    path('<int:order_id>/attachments/', AttachmentListView.as_view(), name='order-attachment-list'),
    path('<int:order_id>/attachments/<int:pk>/', AttachmentDetailView.as_view(), name='order-attachment-detail'),
    
    # Specialized order endpoints
    path('pickup-delivery/', PickupDeliveryOrderCreateView.as_view(), name='pickup-delivery-order'),
    path('cargo-delivery/', CargoDeliveryOrderView.as_view(), name='cargo-delivery-order'),
    path('pending/', PendingOrdersView.as_view(), name='pending-orders'),
    path('assigned/', AssistantOrdersView.as_view(), name='assistant-orders'),
    path('available/', AvailableOrdersView.as_view(), name='available-orders'),
    path('assistant/', AssistantOrdersAPIView.as_view(), name='assistant-orders-api'),
    path('handler/all/', HandlerAllOrdersView.as_view(), name='handler-all-orders'),

    # New endpoints for tracking, feedback, reporting, referral
    path('<int:pk>/tracking/', OrderTrackingView.as_view(), name='order-tracking'),
    path('<int:pk>/tracking/initialize/', InitializeTrackingView.as_view(), name='initialize-tracking'),
    path('<int:order_id>/client-feedback/', ClientFeedbackCreateView.as_view(), name='client-feedback-create'),
    path('client-feedback/<int:pk>/', ClientFeedbackDetailView.as_view(), name='client-feedback-detail'),
    path('<int:order_id>/rider-feedback/', RiderFeedbackCreateView.as_view(), name='rider-feedback-create'),
    path('rider-feedback/<int:pk>/', RiderFeedbackDetailView.as_view(), name='rider-feedback-detail'),
    path('<int:order_id>/cargo-photos/', CargoPhotoUploadView.as_view(), name='cargo-photo-upload'),
    path('cargo-value/<int:pk>/', CargoValueView.as_view(), name='cargo-value'),
    path('<int:order_id>/report-issue/', ReportIssueCreateView.as_view(), name='report-issue-create'),
    path('report-issues/', ReportIssueListView.as_view(), name='report-issue-list'),
    path('referrals/', ReferralListView.as_view(), name='referral-list'),
    path('referrals/create/', ReferralCreateView.as_view(), name='referral-create'),
    
    # Tracking waypoints and events endpoints
    path('tracking/<int:tracking_id>/waypoints/', TrackingWaypointListCreateView.as_view(), name='tracking-waypoint-list'),
    path('tracking/waypoints/<int:pk>/', TrackingWaypointDetailView.as_view(), name='tracking-waypoint-detail'),
    path('tracking/<int:tracking_id>/events/', TrackingEventListCreateView.as_view(), name='tracking-event-list'),
    path('tracking/events/<int:pk>/', TrackingEventDetailView.as_view(), name='tracking-event-detail'),
    path('tracking/<int:tracking_id>/history/', TrackingLocationHistoryListView.as_view(), name='tracking-location-history'),

    # Banking endpoints
    path('banking/banks/', BankListView.as_view(), name='bank-list'),
    path('banking/orders/', BankingOrderListCreateView.as_view(), name='banking-order-list-create'),
    path('banking/orders/<int:pk>/', BankingOrderDetailView.as_view(), name='banking-order-detail'),
    path('banking/orders/<int:pk>/cancel/', BankingOrderCancelView.as_view(), name='banking-order-cancel'),

    path('handyman/service-types/', HandymanServiceTypeListView.as_view(), name='handyman-service-type-list'),
    path('handyman/orders/', HandymanOrderListCreateView.as_view(), name='handyman-order-list-create'),
    path('handyman/orders/<int:pk>/', HandymanOrderDetailView.as_view(), name='handyman-order-detail'),
    path('handyman/orders/<int:pk>/status/', HandymanOrderStatusUpdateView.as_view(), name='handyman-order-status-update'),
    path('handyman/orders/<int:pk>/assign/', AssignHandymanOrderView.as_view(), name='handyman-order-assign'),
    path('handyman/orders/<int:pk>/quote/', HandymanServiceQuoteView.as_view(), name='handyman-service-quote'),
    path('handyman/orders/<int:handyman_order_id>/final-payment/', HandymanServiceFinalPaymentView.as_view(), name='handyman-final-payment'),
    path('handyman/orders/<int:order_id>/images/', HandymanOrderImageUploadView.as_view(), name='handyman-order-image-upload'),
    path('handyman/orders/pending/', PendingHandymanOrdersView.as_view(), name='handyman-pending-orders'),
    path('handyman/orders/assigned/', AssistantHandymanOrdersView.as_view(), name='handyman-assistant-orders'),
    path('deployment-check/', deployment_check_view, name='deployment-check'),
    
    # Quote Management URLs
    path('quotes/', ServiceProviderQuoteListView.as_view(), name='service-provider-quotes'),
    path('quotes/<int:pk>/', ServiceProviderQuoteDetailView.as_view(), name='service-provider-quote-detail'),
    path('quotes/<int:quote_id>/submit/', SubmitQuoteView.as_view(), name='submit-quote'),
    path('quotes/<int:quote_id>/images/', QuoteImageUploadView.as_view(), name='quote-image-upload'),
    path('quotes/status-check/<int:order_id>/', quote_status_check, name='quote-status-check'),
    
    # Handler Quote Management
    path('handler/quotes/', HandlerQuoteManagementView.as_view(), name='handler-quotes'),
    path('handler/quotes/<int:quote_id>/review/', ApproveRejectQuoteView.as_view(), name='approve-reject-quote'),
    
    # Order with Quotes
    path('handyman/orders/<int:pk>/quotes/', HandymanOrderQuotesView.as_view(), name='handyman-order-quotes'),
    
    # Service Provider Dashboard
    path('service-provider/dashboard/', ServiceProviderDashboardView.as_view(), name='service-provider-dashboard'),
    
    # Payment endpoints (NCBA Till API)
    path('payments/initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/<int:pk>/', PaymentStatusView.as_view(), name='payment-status'),
    path('payments/<int:payment_id>/process/', NCBAPaymentView.as_view(), name='process-payment'),
    path('payments/ncba/callback/', NCBACallbackView.as_view(), name='ncba-callback'),
    path('payments/ncba/qr-generate/', NCBAQRGenerationView.as_view(), name='ncba-qr-generate'),
    path('payments/<int:payment_id>/cancel/', PaymentCancellationView.as_view(), name='cancel-payment'),
    path('<int:order_id>/payment-status/', OrderPaymentStatusView.as_view(), name='order-payment-status'),
    
    # Price calculation endpoints
    path('calculate-price/', PriceCalculationView.as_view(), name='calculate-price'),
    path('<int:pk>/update_price_realtime/', OrderPriceRealtimeUpdateView.as_view(), name='order-price-realtime-update'),
]

