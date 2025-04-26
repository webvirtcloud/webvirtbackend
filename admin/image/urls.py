from django.urls import re_path

from .views import AdminImageDataView, AdminImageIndexView, AdminImageResetEventAction

urlpatterns = [
    re_path(r"$", AdminImageIndexView.as_view(), name="admin_image_index"),
    re_path(r"^(?P<pk>\d+)/$", AdminImageDataView.as_view(), name="admin_image_data"),
    re_path(r"^(?P<pk>\d+)/reset_event/$", AdminImageResetEventAction.as_view(), name="admin_image_reset_event"),
]
