from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Banks, BankingOrder
from .serializers import BankSerializer, BankingOrderSerializer

class BankListView(generics.ListAPIView):
    """
    API endpoint to list all active banks.
    """
    queryset = Banks.objects.filter(is_active=True).order_by('name')
    serializer_class = BankSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow anonymous access for testing

class BankingOrderListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create banking orders.
    """
    serializer_class = BankingOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return BankingOrder.objects.filter(user=user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        print(f"Request data: {request.data}")
        try:
            # Get the bank name from the request
            bank_name = request.data.get('bank')
            print(f"Bank name: {bank_name}")
            
            # Try to get the bank by name or create it if it doesn't exist
            try:
                bank = Banks.objects.get(name=bank_name)
                print(f"Found bank: {bank.id} - {bank.name}")
            except Banks.DoesNotExist:
                bank = Banks.objects.create(
                    name=bank_name,
                    description=f"{bank_name} Bank",
                    is_active=True
                )
                print(f"Created bank: {bank.id} - {bank.name}")
            
            # Replace the bank name with the bank ID
            mutable_data = request.data.copy()
            mutable_data['bank'] = bank.id
            
            serializer = self.get_serializer(data=mutable_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"Error creating banking order: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        # Get the client user (can be different if handler is placing order for client)
        from .views import get_client_user
        client = get_client_user(self.request)
        serializer.save(user=client)

class BankingOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update or delete a banking order.
    """
    serializer_class = BankingOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return BankingOrder.objects.filter(user=user)

class BankingOrderCancelView(APIView):
    """
    API endpoint to cancel a pending banking order.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            order = BankingOrder.objects.get(pk=pk, user=request.user)
        except BankingOrder.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 'pending':
            return Response({"detail": "Only pending orders can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.save()
        serializer = BankingOrderSerializer(order)
        return Response(serializer.data)
