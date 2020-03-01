from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from app.models import *


class InventorySellViewTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='sword')
        self.user = User.objects.create_user(username='ben', password='abc')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_invalid_request(self):
        InventoryItem.objects.create(user=self.user, item=self.item, count=10)
        response = self.client.post(reverse('api:inventory_sell', kwargs={'pk': 1}), data={'count': 10})
        self.assertEqual(400, response.status_code)

    def test_make_listing(self):
        InventoryItem.objects.create(user=self.user, item=self.item, count=10)
        response = self.client.post(reverse('api:inventory_sell', kwargs={'pk': 1}), data={'count': 10, 'price': 5})
        self.assertEqual(200, response.status_code)
        self.assertEqual(10, response.data['count'])
        self.assertEqual(5, response.data['price'])

    def test_user_does_not_have_items(self):
        InventoryItem.objects.create(user=self.user, item=self.item, count=10)
        response = self.client.post(reverse('api:inventory_sell', kwargs={'pk': 1}), data={'count': 20, 'price': 5})
        self.assertEqual(400, response.status_code)
