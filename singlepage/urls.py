from django.urls import path
from .views import IndexView
from django.views.decorators.cache import never_cache

urlpatterns = [
    path('', never_cache(IndexView.as_view()), name='index'),
]