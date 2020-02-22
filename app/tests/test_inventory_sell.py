from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Item, InventoryItem


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