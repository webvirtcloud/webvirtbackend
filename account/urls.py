from django.urls import path

from .views import ObtainAuthToken

urlpatterns = [
    path('login/', ObtainAuthToken.as_view(), name='login'),
]
