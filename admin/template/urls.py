from django.urls import re_path
from .views import AdminImageIndexView, AdminImageCreateView, AdminImageUpdateView, AdminImageDeleteView


urlpatterns = [
    re_path(r"$", AdminImageIndexView.as_view(), name="admin_template_index"),
    re_path(r"create/?$", AdminImageCreateView.as_view(), name="admin_template_create"),
    re_path(r"update/(?P<pk>\d+)/?$", AdminImageUpdateView.as_view(), name="admin_template_update"),
    re_path(r"delete/(?P<pk>\d+)/?$", AdminImageDeleteView.as_view(), name="admin_template_delete"),
]
