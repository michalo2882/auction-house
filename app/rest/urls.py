from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('items', views.ItemViewSet)
router.register('inventory', views.InventoryItemViewSet, basename='inventory')

app_name = 'api'
urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('inventory/<int:pk>/sell', views.inventory_sell, name='inventory_sell'),
    path('listing/<int:pk>/cancel', views.listing_cancel, name='listing_cancel'),
    path('item/<int:pk>/listings', views.item_listings, name='item_listings'),
    path('item/<int:pk>/create-listing', views.item_create_buy_listing, name='item_create_buy_listing'),
    path('item/<int:pk>/buy', views.item_buy, name='item_buy'),
    path('', include(router.urls)),
]
