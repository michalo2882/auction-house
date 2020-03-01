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
        fields = ['name']


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ['user', 'item', 'count', 'description']


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['item', 'count', 'price', 'direction', 'submitter', 'description']


class SellRequestSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    price = serializers.IntegerField()
