from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.errors import FailedToCreateListingError
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


class SellListingTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_not_enough_items(self):
        inventory_item = InventoryItem.objects.create(user=self.user, item=self.item, count=1)

        with self.assertRaises(FailedToCreateListingError) as cm:
            inventory_item.make_sell_listing(count=5, price=10)
        self.assertEqual(cm.exception.msg, 'User does not have enough items')

    def test_buy_price_is_higher(self):
        inventory_item = InventoryItem.objects.create(user=self.user, item=self.item, count=5)
        Listing.objects.create(item=self.item, count=5, price=20, direction=Listing.Direction.BUY, submitter=self.user)

        with self.assertRaises(FailedToCreateListingError) as cm:
            inventory_item.make_sell_listing(count=5, price=10)
        self.assertEqual(cm.exception.msg, 'Cannot make listing when sell price is lower than highest buy listing')

    def test_successful_listing(self):
        inventory_item = InventoryItem.objects.create(user=self.user, item=self.item, count=20)
        inventory_item.make_sell_listing(count=5, price=10)

        listings = list(Listing.objects.all())
        self.assertEqual(1, len(listings))
        self.assertEqual(self.item, listings[0].item)
        self.assertEqual(5, listings[0].count)
        self.assertEqual(10, listings[0].price)
        self.assertEqual(Listing.Direction.SELL, listings[0].direction)
        self.assertEqual(self.user, listings[0].submitter)

        inventory_item.refresh_from_db()
        self.assertEqual(15, inventory_item.count)


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


class InventorySellTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_unauthorized(self):
        response = self.client.get(reverse('app:inventory_sell', kwargs={'pk': 3}))
        self.assertRedirects(response, '/accounts/login/?next=/inventory/3/sell')

    def test_not_found(self):
        self.client.login(username='ben', password='abc')
        response = self.client.get(reverse('app:inventory_sell', kwargs={'pk': 3}))
        self.assertEqual(404, response.status_code)

    def test_successful_get(self):
        self.client.login(username='ben', password='abc')
        InventoryItem.objects.create(user=self.user, item=self.item, count=20)
        response = self.client.get(reverse('app:inventory_sell', kwargs={'pk': 1}))
        self.assertEqual(200, response.status_code)

    def test_successful_post(self):
        self.client.login(username='ben', password='abc')
        InventoryItem.objects.create(user=self.user, item=self.item, count=20)
        response = self.client.post(reverse('app:inventory_sell', kwargs={'pk': 1}),
                                    data={'count': 20, 'price': 50})
        self.assertRedirects(response, '/')
