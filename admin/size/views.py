from django import forms
from django.urls import reverse_lazy
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import InlineCheckboxes

from size.models import Size
from region.models import Region
from .filters import SizeFilter
from .tables import SizeHTMxTable
from .forms import FormSize, CustomModelMultipleChoiceField
from admin.mixins import AdminView, AdminFormView, AdminUpdateView, AdminDeleteView


class AdminSizeIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = SizeHTMxTable
    filterset_class = SizeFilter
    template_name = "admin/size/index.html"

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminSizeCreateView(AdminFormView):
    template_name = "admin/size/create.html"
    form_class = FormSize
    success_url = reverse_lazy("admin_size_index")

    def form_valid(self, form):
        if form.cleaned_data["type"] == Size.LBAAS:
            if Size.objects.filter(type=Size.LBAAS, is_deleted=False).exists():
                form.add_error("type", "LBaaS already exists.")
                return self.form_invalid(form)
        form.instance.disk = form.cleaned_data["disk"] * (1024**3)
        form.instance.memory = form.cleaned_data["memory"] * (1024**2)
        form.instance.transfer = form.cleaned_data["transfer"] * (1024**4)
        form.save()
        return super().form_valid(form)


class AdminSizeUpdateView(AdminUpdateView):
    template_name = "admin/size/update.html"
    template_name_suffix = "_form"
    model = Size
    success_url = reverse_lazy("admin_size_index")
    fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AdminSizeUpdateView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            "name",
            "slug",
            "description",
            "vcpu",
            "disk",
            "memory",
            "transfer",
            "price",
            InlineCheckboxes("regions", css_class="checkboxinput"),
            "is_active",
        )

    def get_form(self, form_class=None):
        form = super(AdminSizeUpdateView, self).get_form(form_class)
        form.fields["type"].required = False
        form.fields["regions"] = CustomModelMultipleChoiceField(
            queryset=Region.objects.filter(is_deleted=False), widget=forms.CheckboxSelectMultiple(), required=False
        )
        form.fields["price"].label = "Price (Hourly)"
        form.fields["disk"].label = "Disk (GB)"
        form.fields["disk"].widget = forms.NumberInput(attrs={"step": "1"})
        form.initial["disk"] = form.initial["disk"] // (1024**3)

        form.fields["memory"].label = "Memory (MB)"
        form.initial["memory"] = form.initial["memory"] // (1024**2)
        form.fields["memory"].widget = forms.NumberInput(attrs={"step": "1"})

        form.fields["transfer"].label = "Transfer (TB)"
        form.initial["transfer"] = form.initial["transfer"] // (1024**4)
        form.fields["transfer"].widget = forms.NumberInput(attrs={"step": "1"})
        return form

    def form_valid(self, form):
        form.instance.disk = form.cleaned_data["disk"] * (1024**3)
        form.instance.memory = form.cleaned_data["memory"] * (1024**2)
        form.instance.transfer = form.cleaned_data["transfer"] * (1024**4)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(AdminSizeUpdateView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context


class AdminSizeDeleteView(AdminDeleteView):
    template_name = "admin/size/delete.html"
    model = Size
    success_url = reverse_lazy("admin_size_index")

    def delete(self, request, *args, **kwargs):
        size = self.get_object()
        size.delete()
        return super(self).delete(request, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(AdminSizeDeleteView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_context_data(self, **kwargs):
        context = super(AdminSizeDeleteView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context
