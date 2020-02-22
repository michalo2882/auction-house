from django.contrib.auth.models import User
from django.test import TestCase

from app.errors import FailedToMakeTransactionError
from app.models import Item, Listing, Wallet, InventoryItem


class ItemBuyTransactionTests(TestCase):
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