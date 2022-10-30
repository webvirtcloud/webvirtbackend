from django.urls import re_path

from .views import Login, Register, ResetPassword, ResetPasswordHash

urlpatterns = [
    re_path(r'login/?$', Login.as_view(), name='login'),
    re_path(r'register/?$', Register.as_view(), name='register'),
    re_path(r'reset_password/?$', ResetPassword.as_view(), name='reset_password'),
    re_path(r'reset_password/(?P<hash>\w+)/?$', ResetPasswordHash.as_view(), name='reset_password_hash'),
]
