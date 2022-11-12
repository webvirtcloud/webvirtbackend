from django.urls import include, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from project.views import ProjectListAPI

urlpatterns = [
    re_path(r"$", ProjectListAPI.as_view(), name="project_list_api"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
