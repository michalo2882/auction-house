from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views import generic

from app.models import Wallet, Item, Listing, InventoryItem


class ItemsView(generic.ListView):
    model = Item
    template_name = 'app/items.html'


@login_required
def dashboard(request):
    sell_listings = Listing.objects.filter(submitter=request.user, direction=Listing.Direction.SELL).order_by('-pk')
    buy_listings = Listing.objects.filter(submitter=request.user, direction=Listing.Direction.BUY).order_by('-pk')
    inventory_items = InventoryItem.objects.filter(user=request.user)
    return render(request, 'app/dashboard.html', {
        'wallet': Wallet.get_users_wallet(request.user),
        'sell_listings': sell_listings,
        'buy_listings': buy_listings,
        'inventory_items': inventory_items,
    })
