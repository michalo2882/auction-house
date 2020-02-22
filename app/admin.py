from django.contrib import admin

from .models import *

admin.site.register(Wallet)
admin.site.register(Item)
admin.site.register(InventoryItem)
