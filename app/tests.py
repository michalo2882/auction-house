from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.errors import FailedToCreateListingError, FailedToMakeTransactionError, CannotAffordError, \
    InvalidTransactionError
from app.models import Wallet, Item, InventoryItem, Listing


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


class ListingTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')

    def test_process_purchase_invalid(self):
        listing = Listing.objects.create(item=self.item, count=5, price=10, direction=Listing.Direction.BUY,
                                         submitter=self.user)
        with self.assertRaises(InvalidTransactionError):
            listing.process_purchase(5)

    def test_process_purchase_too_many_items(self):
        listing = Listing.objects.create(item=self.item, count=5, price=10, direction=Listing.Direction.SELL,
                                         submitter=self.user)
        with self.assertRaises(ValueError):
            listing.process_purchase(10)

    def test_process_purchase_updates_listing(self):
        listing = Listing.objects.create(item=self.item, count=5, price=10, direction=Listing.Direction.SELL,
                                         submitter=self.user)
        listing.process_purchase(1)
        listing.refresh_from_db()
        self.assertEqual(4, listing.count)

    def test_process_purchase_deletes_listing(self):
        listing = Listing.objects.create(item=self.item, count=5, price=10, direction=Listing.Direction.SELL,
                                         submitter=self.user)
        listing.process_purchase(5)
        self.assertEqual(0, Listing.objects.all().count())


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


class BuyTransactionTests(TestCase):
    def setUp(self) -> None:
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')
        self.seller = User.objects.create_user(username='jon', password='abc')

    def test_no_listings(self):
        with self.assertRaises(FailedToMakeTransactionError) as cm:
            self.item.make_buy_transaction(self.user, count=5)
        self.assertEqual(cm.exception.msg, 'No listings')

    def test_user_has_no_coins(self):
        listing = Listing.objects.create(item=self.item, count=5, price=10, direction=Listing.Direction.SELL,
                                         submitter=self.seller)

        result = self.item.make_buy_transaction(self.user, count=5)
        self.assertEquals(0, result['items_purchased'])
        self.assertEquals(0, result['coins_spent'])

        self.assertEqual(0, Wallet.get_users_wallet(self.user).coins)
        self.assertEqual(0, Wallet.get_users_wallet(self.seller).coins)
        self.assertFalse(InventoryItem.objects.filter(user=self.user, item=self.item).exists())
        self.assertEqual(listing, Listing.objects.get(pk=listing.pk))

    def test_success_listing_deleted(self):
        Listing.objects.create(item=self.item, count=5, price=10, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(50)

        result = self.item.make_buy_transaction(self.user, count=5)
        self.assertEquals(5, result['items_purchased'])
        self.assertEquals(50, result['coins_spent'])

        self.assertEqual(0, Wallet.get_users_wallet(self.user).coins)
        self.assertEqual(50, Wallet.get_users_wallet(self.seller).coins)
        self.assertEqual(5, InventoryItem.objects.get(user=self.user, item=self.item).count)
        self.assertFalse(Listing.objects.filter(item=self.item).exists())

    def test_success_listing_remains(self):
        Listing.objects.create(item=self.item, count=20, price=10, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(50)

        result = self.item.make_buy_transaction(self.user, count=5)
        self.assertEquals(5, result['items_purchased'])
        self.assertEquals(50, result['coins_spent'])

        self.assertEqual(0, Wallet.get_users_wallet(self.user).coins)
        self.assertEqual(50, Wallet.get_users_wallet(self.seller).coins)
        self.assertEqual(5, InventoryItem.objects.get(user=self.user, item=self.item).count)
        self.assertEqual(15, Listing.objects.filter(item=self.item).first().count)

    def test_success_multiple_listings(self):
        Listing.objects.create(item=self.item, count=20, price=20, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        Listing.objects.create(item=self.item, count=20, price=10, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(200 + 100)

        result = self.item.make_buy_transaction(self.user, count=25)
        self.assertEquals(25, result['items_purchased'])
        self.assertEquals(200 + 100, result['coins_spent'])

        self.assertEqual(0, Wallet.get_users_wallet(self.user).coins)
        self.assertEqual(300, Wallet.get_users_wallet(self.seller).coins)
        self.assertEqual(25, InventoryItem.objects.get(user=self.user, item=self.item).count)
        self.assertEqual(1, Listing.objects.filter(item=self.item).count())
        self.assertEqual(15, Listing.objects.filter(item=self.item).first().count)
        self.assertEqual(20, Listing.objects.filter(item=self.item).first().price)

    def test_partial_success_not_enough_coins(self):
        Listing.objects.create(item=self.item, count=20, price=20, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        Listing.objects.create(item=self.item, count=20, price=10, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(220)

        result = self.item.make_buy_transaction(self.user, count=25)
        self.assertEquals(20, result['items_purchased'])
        self.assertEquals(200, result['coins_spent'])

        self.assertEqual(20, Wallet.get_users_wallet(self.user).coins)
        self.assertEqual(200, Wallet.get_users_wallet(self.seller).coins)
        self.assertEqual(20, InventoryItem.objects.get(user=self.user, item=self.item).count)
        self.assertEqual(1, Listing.objects.filter(item=self.item).count())
        self.assertEqual(20, Listing.objects.filter(item=self.item).first().count)
        self.assertEqual(20, Listing.objects.filter(item=self.item).first().price)

    def test_partial_success_not_enough_listings(self):
        Listing.objects.create(item=self.item, count=20, price=20, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        Listing.objects.create(item=self.item, count=20, price=10, direction=Listing.Direction.SELL,
                               submitter=self.seller)
        wallet = Wallet.get_users_wallet(self.user)
        wallet.add(800)

        result = self.item.make_buy_transaction(self.user, count=50)
        self.assertEquals(40, result['items_purchased'])
        self.assertEquals(200 + 400, result['coins_spent'])

        self.assertEqual(200, Wallet.get_users_wallet(self.user).coins)
        self.assertEqual(600, Wallet.get_users_wallet(self.seller).coins)
        self.assertEqual(40, InventoryItem.objects.get(user=self.user, item=self.item).count)
        self.assertEqual(0, Listing.objects.filter(item=self.item).count())
