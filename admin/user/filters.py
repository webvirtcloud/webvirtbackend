import django_filters
from django.db.models import Q

from account.models import User


class UserFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = User
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return User.objects.filter(
            Q(email__icontains=value) | Q(first_name__icontains=value) | Q(last_name__icontains=value), is_admin=False
        )
