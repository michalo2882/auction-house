from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic

from app.errors import FailedToCreateListingError
from app.forms import CreateListingForm
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


@login_required
def inventory_sell(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    sell_listings = Listing.objects.filter(item=inventory_item.item, direction=Listing.Direction.SELL).order_by('price')
    buy_listings = Listing.objects.filter(item=inventory_item.item, direction=Listing.Direction.BUY).order_by('-price')
    error_message = None
    if request.method == 'POST':
        form = CreateListingForm(request.POST)
        if form.is_valid():
            try:
                inventory_item.make_sell_listing(form.cleaned_data['count'],
                                                 form.cleaned_data['price'])
                return redirect('app:dashboard')
            except FailedToCreateListingError as e:
                error_message = e.msg
    else:
        form = CreateListingForm()
    return render(request, 'app/inventory_sell.html', {
        'inventory_item': inventory_item,
        'item': inventory_item.item,
        'sell_listings': sell_listings,
        'buy_listings': buy_listings,
        'form': form,
        'error_message': error_message
    })
