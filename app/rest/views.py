from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from app.rest.permissions import IsOwner
from app.rest.serializers import *


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    sell_listings = Listing.objects.filter(submitter=request.user, direction=Listing.Direction.SELL).order_by('-pk')
    buy_listings = Listing.objects.filter(submitter=request.user, direction=Listing.Direction.BUY).order_by('-pk')
    inventory_items = InventoryItem.objects.filter(user=request.user)
    return Response({
        'user': request.user.username,
        'wallet': WalletSerializer(Wallet.get_users_wallet(request.user)).data,
        'sellListings': ListingSerializer(sell_listings, many=True).data,
        'buyListings': ListingSerializer(buy_listings, many=True).data,
        'inventory': InventoryItemSerializer(inventory_items, many=True).data,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def inventory_sell(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    serializer = ListingRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            listing = inventory_item.make_sell_listing(serializer.data['count'],
                                                       serializer.data['price'])
            return Response(ListingSerializer(listing).data)
        except FailedToCreateListingError as e:
            return Response({'error': e.msg}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def item_listings(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return Response({
        'buyListings': ListingSerializer(
            Listing.objects.filter(item=item, direction=Listing.Direction.BUY).order_by('-price'), many=True).data,
        'sellListings': ListingSerializer(
            Listing.objects.filter(item=item, direction=Listing.Direction.SELL).order_by('price'), many=True).data,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def item_create_buy_listing(request, pk):
    item = get_object_or_404(Item, pk=pk)
    serializer = ListingRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            listing = item.make_buy_listing(request.user,
                                            count=serializer.data['count'],
                                            price=serializer.data['price'])
            return Response(ListingSerializer(listing).data)
        except FailedToCreateListingError as e:
            return Response({'error': e.msg}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def item_buy(request, pk):
    item = get_object_or_404(Item, pk=pk)
    serializer = ItemBuyRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = item.make_buy_transaction(request.user, serializer.data['count'])
            return Response(result)
        except FailedToMakeTransactionError as e:
            return Response({'error': e.msg}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class InventoryItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return InventoryItem.objects.filter(user=self.request.user)
