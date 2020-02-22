from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('items', views.ItemsView.as_view(), name='items'),
    path('item/<int:pk>/buy', views.item_buy, name='item_buy'),
    path('inventory/<int:pk>/sell', views.inventory_sell, name='inventory_sell'),
]
