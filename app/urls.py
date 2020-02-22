from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('items', views.ItemsView.as_view(), name='items'),
]
