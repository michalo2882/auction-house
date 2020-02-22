from django.contrib.auth.models import User
from django.test import TestCase

from app.errors import FailedToCreateListingError
from app.models import Item, InventoryItem, Listing


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