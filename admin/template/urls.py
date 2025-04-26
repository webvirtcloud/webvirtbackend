from django.urls import re_path

from .views import AdminTemplateCreateView, AdminTemplateDeleteView, AdminTemplateIndexView, AdminTemplateUpdateView

urlpatterns = [
    re_path(r"$", AdminTemplateIndexView.as_view(), name="admin_template_index"),
    re_path(r"create/?$", AdminTemplateCreateView.as_view(), name="admin_template_create"),
    re_path(r"update/(?P<pk>\d+)/?$", AdminTemplateUpdateView.as_view(), name="admin_template_update"),
    re_path(r"delete/(?P<pk>\d+)/?$", AdminTemplateDeleteView.as_view(), name="admin_template_delete"),
]
