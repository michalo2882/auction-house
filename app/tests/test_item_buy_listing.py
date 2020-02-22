from django.test import TestCase

from app.models import *


class BuyListingTests(TestCase):
    def test_user_has_not_enough_money(self):
        item = Item.objects.create(name='sword')
        user = User.objects.create_user(username='ben', password='abc')

        with self.assertRaises(FailedToCreateListingError) as cm:
            item.make_buy_listing(user, count=5, price=20)
        self.assertEqual(cm.exception.msg, 'User does not have enough money')

    def test_sell_price_is_lower(self):
        item = Item.objects.create(name='sword')
        user = User.objects.create_user(username='ben', password='abc')
        wallet = Wallet.get_users_wallet(user)
        wallet.coins = 20
        wallet.save()
        InventoryItem.objects.create(user=user, item=item, count=5)
        Listing.objects.create(item=item, count=5, price=10, direction=Listing.Direction.SELL, submitter=user)

        with self.assertRaises(FailedToCreateListingError) as cm:
            item.make_buy_listing(user, count=5, price=20)
        self.assertEqual(cm.exception.msg, 'Cannot make listing when buy price is higher than lowest sell listing')

    def test_successful_listing(self):
        item = Item.objects.create(name='sword')
        user = User.objects.create_user(username='ben', password='abc')
        wallet = Wallet.get_users_wallet(user)
        wallet.coins = 20
        wallet.save()

        item.make_buy_listing(user, count=5, price=10)

        listings = list(Listing.objects.all())
        self.assertEqual(1, len(listings))
        self.assertEqual(item, listings[0].item)
        self.assertEqual(5, listings[0].count)
        self.assertEqual(10, listings[0].price)
        self.assertEqual(Listing.Direction.BUY, listings[0].direction)
        self.assertEqual(user, listings[0].submitter)

        wallet.refresh_from_db()
        self.assertEqual(10, wallet.coins)
