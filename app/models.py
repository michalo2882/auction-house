from django.contrib.auth.models import User
from django.db import models, transaction

from app.errors import FailedToCreateListingError


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coins = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user}-has-{self.coins}'

    @staticmethod
    def get_users_wallet(user: User):
        try:
            return Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return Wallet.objects.create(user=user)


class Item(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    @transaction.atomic
    def add_to_user_inventory(self, user: User, count):
        try:
            inventory_item = InventoryItem.objects.get(user=user, item=self)
            inventory_item.count += count
            inventory_item.save()
            return inventory_item
        except InventoryItem.DoesNotExist:
            return InventoryItem.objects.create(user=user, item=self, count=count)


class InventoryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    count = models.IntegerField()

    def __str__(self):
        return f'{self.user}-{self.item}-{self.count}'

    def description(self):
        return f'{self.count} of "{self.item}"'

    @transaction.atomic
    def make_sell_listing(self, count, price):
        if self.count < count:
            raise FailedToCreateListingError("User does not have enough items")

        listing = Listing.objects.filter(item=self.item, direction=Listing.Direction.BUY).order_by('-price').first()
        if listing and listing.price >= price:
            raise FailedToCreateListingError("Cannot make listing when sell price is lower than highest buy listing")

        self.count -= count
        self.save()

        return Listing.objects.create(item=self.item, count=count, price=price, direction=Listing.Direction.SELL,
                                      submitter=self.user)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'item'], name='unique-user-item')
        ]


class Listing(models.Model):
    Direction = models.IntegerChoices('Direction', 'BUY SELL')
    int_to_direction = {k: v for k, v in Direction.choices}

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    count = models.IntegerField()
    price = models.IntegerField()
    direction = models.IntegerField(choices=Direction.choices)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.item.name}-{self.count}-{self.price}-{self.int_to_direction[self.direction]}-{self.submitter}'

    def description(self):
        return f'{self.count} of "{self.item}" for {self.price} coins'
