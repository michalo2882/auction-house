from django.contrib.auth.models import User
from django.db import models, transaction

from app.errors import FailedToCreateListingError, FailedToMakeTransactionError, CannotAffordError, \
    InvalidTransactionError


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

    @transaction.atomic
    def add(self, coins):
        self.refresh_from_db()
        self.coins += coins
        self.save()

    @transaction.atomic
    def spend(self, coins):
        self.refresh_from_db()
        if coins > self.coins:
            raise CannotAffordError()
        self.coins -= coins
        self.save()


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

    @transaction.atomic
    def make_buy_transaction(self, user: User, count):
        wallet = Wallet.get_users_wallet(user)
        remaining_purchase_count = count
        coins_spent = 0
        listings = Listing.objects.filter(item=self, direction=Listing.Direction.SELL).order_by('price')
        if not listings:
            raise FailedToMakeTransactionError('No listings')
        for listing in listings:
            if listing.count > remaining_purchase_count:
                take = remaining_purchase_count
            else:
                take = listing.count

            price = take * listing.price

            try:
                wallet.spend(price)
            except CannotAffordError:
                # TODO: make partial purchase
                break

            coins_spent += price
            remaining_purchase_count -= take

            listing.process_purchase(take)

        items_purchased = count - remaining_purchase_count
        if items_purchased:
            self.add_to_user_inventory(user, items_purchased)
        return {
            'items_purchased': items_purchased,
            'coins_spent': coins_spent
        }

    @transaction.atomic
    def make_buy_listing(self, user: User, count, price):
        wallet = Wallet.get_users_wallet(user)

        if wallet.coins < price:
            raise FailedToCreateListingError("User does not have enough money")

        listing = Listing.objects.filter(item=self, direction=Listing.Direction.SELL).order_by('price').first()
        if listing and listing.price <= price:
            raise FailedToCreateListingError("Cannot make listing when buy price is higher than lowest sell listing")

        wallet.spend(price)

        return Listing.objects.create(item=self, count=count, price=price, direction=Listing.Direction.BUY,
                                      submitter=user)


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

    @transaction.atomic
    def process_purchase(self, count):
        if self.direction != Listing.Direction.SELL:
            raise InvalidTransactionError()
        if count > self.count:
            raise ValueError("Cannot take more items than listed")
        wallet = Wallet.get_users_wallet(self.submitter)
        wallet.add(self.price * count)
        self.count -= count
        if not self.count:
            self.delete()
        else:
            self.save()

    @transaction.atomic
    def cancel(self):
        if self.direction == Listing.Direction.BUY:
            wallet = Wallet.get_users_wallet(self.submitter)
            wallet.add(self.price * self.count)
        else:
            self.item.add_to_user_inventory(self.submitter, self.count)
        self.delete()
