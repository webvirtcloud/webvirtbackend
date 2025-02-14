from django.urls import reverse
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from crispy_forms.helper import FormHelper

from account.models import User
from billing.models import Balance
from firewall.models import Firewall
from image.models import SnapshotCounter
from virtance.models import VirtanceCounter
from floating_ip.models import FloatIPCounter
from .forms import FormUser
from .filters import UserFilter, UserBillingFilter
from .tables import UserHTMxTable, UserBillingHTMxTable
from admin.mixins import AdminView, AdminTemplateView, AdminFormView, AdminUpdateView


class AdminUserIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = UserHTMxTable
    filterset_class = UserFilter
    template_name = "admin/user/index.html"

    def get_queryset(self):
        return User.objects.filter(is_admin=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminUserCreateView(AdminFormView):
    template_name = "admin/user/create.html"
    form_class = FormUser
    success_url = reverse_lazy("admin_user_index")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AdminUserUpdateView(AdminUpdateView):
    template_name = "admin/user/update.html"
    template_name_suffix = "_form"
    model = User
    fields = ["first_name", "last_name", "is_active"]

    def __init__(self, *args, **kwargs):
        super(AdminUserUpdateView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_form(self, form_class=None):
        form = super(AdminUserUpdateView, self).get_form(form_class)
        form.fields["is_active"].label = "Active"
        return form

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(AdminUserUpdateView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context

    def get_success_url(self):
        return reverse("admin_user_data", args=[self.kwargs.get("pk")])


class AdminUserDataView(AdminTemplateView):
    template_name = "admin/user/overview.html"

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs.get("pk"), is_admin=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        balance = Balance.objects.filter(user=user).aggregate(balance=Sum("amount"))["balance"] or 0

        month_to_date_usage = 0
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

        # Get firewall usage
        firewalls = Firewall.objects.filter(user=user, is_deleted=False)

        # Get virtance usage
        virtances_counters = VirtanceCounter.objects.filter(
            virtance__user=user,
            started__gte=start_of_month,
            stopped=None,
        )
        virtances_usage = virtances_counters.aggregate(total_amount=Sum("amount"))["total_amount"] or 0

        # Calculate total usage
        month_to_date_usage += virtances_usage

        # Get snapshots usage
        snapshots_counters = SnapshotCounter.objects.filter(
            image__user=user,
            started__gte=start_of_month,
            stopped=None,
        )
        snapshots_usage = snapshots_counters.aggregate(total_amount=Sum("amount"))["total_amount"] or 0

        # Calculate total usage
        month_to_date_usage += snapshots_usage

        # Get floating ip usage
        floating_ips_counters = FloatIPCounter.objects.filter(
            floatip__user=user,
            started__gte=start_of_month,
            stopped=None,
        )
        floating_ips_usage = floating_ips_counters.aggregate(total_amount=Sum("amount"))["total_amount"] or 0

        # Calculate total usage
        month_to_date_usage += floating_ips_usage

        # Calculate total balance with month to date usage
        get_month_to_date_balance = balance + month_to_date_usage

        context["user"] = user
        context["balance"] = balance
        context["firewalls_len"] = len(firewalls)
        context["virtances_len"] = len(virtances_counters)
        context["snapshots_len"] = len(snapshots_counters)
        context["floating_ips_len"] = len(floating_ips_counters)
        context["month_to_date_usage"] = month_to_date_usage
        context["get_month_to_date_balance"] = get_month_to_date_balance
        return context


class AdminUserBillingView(SingleTableMixin, FilterView, AdminView):
    table_class = UserBillingHTMxTable
    filterset_class = UserBillingFilter
    template_name = "admin/user/billing.html"

    def get_object(self):
        return Balance.objects.filter(user_id=self.kwargs.get("pk"))

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["user_id"] = self.kwargs.get("pk")
        return kwargs

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = get_object_or_404(User, pk=self.kwargs.get("pk"), is_admin=False)
        return context
