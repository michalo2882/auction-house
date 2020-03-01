from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('items', views.ItemViewSet)

app_name = 'api'
urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('inventory/<int:pk>/sell', views.inventory_sell, name='inventory_sell'),
    path('', include(router.urls)),
]
