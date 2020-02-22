from django.test import TestCase
from django.urls import reverse

from app.models import *


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


class ItemBuyViewTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_unauthorized(self):
        response = self.client.get(reverse('app:item_buy', kwargs={'pk': 3}))
        self.assertRedirects(response, '/accounts/login/?next=/item/3/buy')

    def test_not_found(self):
        self.client.login(username='ben', password='abc')
        response = self.client.get(reverse('app:item_buy', kwargs={'pk': 3}))
        self.assertEqual(404, response.status_code)

    def test_successful_get(self):
        self.client.login(username='ben', password='abc')
        response = self.client.get(reverse('app:item_buy', kwargs={'pk': 1}))
        self.assertEqual(200, response.status_code)

    def test_buy_listing(self):
        self.client.login(username='ben', password='abc')
        Wallet.get_users_wallet(self.user).add(1000)
        response = self.client.post(reverse('app:item_buy', kwargs={'pk': 1}),
                                    data={'count': 20, 'price': 50, 'create_listing': True})
        self.assertEqual(200, response.status_code)
        listing = Listing.objects.first()
        self.assertIsNotNone(listing)
        self.assertEqual(20, listing.count)
        self.assertEqual(50, listing.price)

    def test_buy_now(self):
        self.client.login(username='ben', password='abc')
        Wallet.get_users_wallet(self.user).add(1000)
        Listing.objects.create(submitter=self.user, item=self.item, count=20, price=50, direction=Listing.Direction.SELL)
        response = self.client.post(reverse('app:item_buy', kwargs={'pk': 1}),
                                    data={'count': 20, 'buy': True})
        self.assertEqual(200, response.status_code)
        inventory_item = InventoryItem.objects.first()
        self.assertIsNotNone(inventory_item)
        self.assertEqual(20, inventory_item.count)
