from django.contrib.auth.models import User
from django.test import TestCase

from app.errors import CannotAffordError
from app.models import Wallet, Item, InventoryItem


class WalletTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_get_users_wallet(self):
        wallet = Wallet.get_users_wallet(self.user)
        self.assertEqual(self.user, wallet.user)
        self.assertEqual(0, wallet.coins)

    def test_add(self):
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(6)
        wallet = Wallet.get_users_wallet(self.user)
        self.assertEqual(6, wallet.coins)

    def test_spend(self):
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(6)
        wallet = Wallet.get_users_wallet(self.user)
        wallet.spend(5)
        wallet = Wallet.get_users_wallet(self.user)
        self.assertEqual(1, wallet.coins)

    def test_spend_should_raise_exception_when_user_does_not_have_enough_coins(self):
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(6)
        with self.assertRaises(CannotAffordError):
            wallet = Wallet.get_users_wallet(self.user)
            wallet.spend(10)


class ItemTests(TestCase):
    def test_add_to_user_inventory(self):
        item = Item.objects.create(name='sword')
        user = User.objects.create_user(username='ben', password='abc')
        item.add_to_user_inventory(user, count=20)
        self.assertEquals(20, InventoryItem.objects.get(user=user, item=item).count)
