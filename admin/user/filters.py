import django_filters
from django.db.models import Q

from account.models import User
from billing.models import Balance


class UserFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = User
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return User.objects.filter(
            Q(email__icontains=value) | Q(first_name__icontains=value) | Q(last_name__icontains=value), is_admin=False
        )


class UserBillingFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Balance
        fields = ["query"]

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop("user_id", None)
        super().__init__(*args, **kwargs)

    def universal_search(self, queryset, name, value):
        return Balance.objects.filter(
            Q(amount__icontains=value) | Q(description__icontains=value),
            user_id=self.user_id,
            user__is_admin=False,
        )
