from django.contrib.auth.models import User
from django.test import TestCase

from app.models import Wallet, Item, InventoryItem


class WalletTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_get_users_wallet(self):
        wallet = Wallet.get_users_wallet(self.user)
        self.assertEqual(self.user, wallet.user)
        self.assertEqual(0, wallet.coins)


class ItemTests(TestCase):
    def test_add_to_user_inventory(self):
        item = Item.objects.create(name='sword')
        user = User.objects.create_user(username='ben', password='abc')
        item.add_to_user_inventory(user, count=20)
        self.assertEquals(20, InventoryItem.objects.get(user=user, item=item).count)
