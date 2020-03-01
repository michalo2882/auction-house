from rest_framework import permissions, mixins, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

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
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    serializer = SellRequestSerializer(data=request.data)
    if serializer.is_valid():
        listing = inventory_item.make_sell_listing(serializer.data['count'],
                                                   serializer.data['price'])
        return Response(ListingSerializer(listing).data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
