from django.contrib.auth.models import User
from django.db import models


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
