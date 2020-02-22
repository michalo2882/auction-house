from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('items', views.ItemViewSet)

app_name = 'api'
urlpatterns = [
    path('dashboard', views.dashboard),
    path('', include(router.urls)),
]
