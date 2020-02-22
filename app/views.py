from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views import generic

from app.models import Wallet, Item


class ItemsView(generic.ListView):
    model = Item
    template_name = 'app/items.html'


@login_required
def dashboard(request):
    return render(request, 'app/dashboard.html', {
        'wallet': Wallet.get_users_wallet(request.user)
    })
