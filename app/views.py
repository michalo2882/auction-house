from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic

from app.errors import FailedToCreateListingError, FailedToMakeTransactionError
from app.forms import CreateListingForm, BuyForm
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
def item_buy(request, pk):
    item = get_object_or_404(Item, pk=pk)
    sell_listings = Listing.objects.filter(item=item, direction=Listing.Direction.SELL).order_by('price')[:20]
    buy_listings = Listing.objects.filter(item=item, direction=Listing.Direction.BUY).order_by('-price')[:20]

    buy_form = BuyForm()
    listing_form = CreateListingForm()
    error_message = None
    success_message = None

    if request.method == 'POST':
        if 'create_listing' in request.POST:
            listing_form = CreateListingForm(request.POST)
            if listing_form.is_valid():
                try:
                    item.make_buy_listing(request.user, count=listing_form.cleaned_data['count'],
                                          price=listing_form.cleaned_data['price'])
                    success_message = 'Listing created'
                except FailedToCreateListingError as e:
                    error_message = e.msg
                    print(error_message)
        else:
            buy_form = BuyForm(request.POST)
            if buy_form.is_valid():
                try:
                    result = item.make_buy_transaction(request.user, buy_form.cleaned_data['count'])
                    success_message = f'Purchased {result["items_purchased"]} item(s) for {result["coins_spent"]} coins'
                except FailedToMakeTransactionError as e:
                    error_message = e.msg

    return render(request, 'app/item_buy.html', {
        'item': item,
        'sell_listings': sell_listings,
        'buy_listings': buy_listings,
        'buy_form': buy_form,
        'listing_form': listing_form,
        'error_message': error_message,
        'success_message': success_message
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
