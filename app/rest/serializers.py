from rest_framework import serializers

from app.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['user', 'coins']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name']


class InventoryItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer()

    class Meta:
        model = InventoryItem
        fields = ['id', 'user', 'item', 'count', 'description']


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['id', 'item', 'count', 'price', 'direction', 'submitter', 'description']


class ListingRequestSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    price = serializers.IntegerField()


class ItemBuyRequestSerializer(serializers.Serializer):
    count = serializers.IntegerField()
