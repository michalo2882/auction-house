from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.models import Wallet


@login_required
def dashboard(request):
    return render(request, 'app/dashboard.html', {
        'wallet': Wallet.get_users_wallet(request.user)
    })
