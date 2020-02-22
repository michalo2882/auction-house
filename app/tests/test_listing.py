from django.contrib.auth.models import User
from django.test import TestCase

from app.errors import InvalidTransactionError
from app.models import Item, Listing


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