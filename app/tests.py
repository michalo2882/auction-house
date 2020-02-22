from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Wallet, Item, InventoryItem, Listing


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


class DashboardViewTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_unauthorized(self):
        response = self.client.get(reverse('app:dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_no_listings(self):
        self.client.login(username='ben', password='abc')
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['sell_listings'], [])
        self.assertQuerysetEqual(response.context['buy_listings'], [])

    def test_listings(self):
        self.client.login(username='ben', password='abc')
        sell = Listing.objects.create(item=self.item, count=10, price=20, direction=Listing.Direction.SELL,
                                      submitter=self.user)
        buy = Listing.objects.create(item=self.item, count=30, price=50, direction=Listing.Direction.BUY,
                                     submitter=self.user)
        response = self.client.get(reverse('app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['sell_listings'], [repr(sell)])
        self.assertQuerysetEqual(response.context['buy_listings'], [repr(buy)])
