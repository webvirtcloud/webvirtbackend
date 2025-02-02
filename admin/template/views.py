from django import forms
from django.db.models import Q
from django.urls import reverse_lazy
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from crispy_forms.layout import Layout
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineCheckboxes

from image.models import Image
from region.models import Region
from .filters import ImageFilter
from .tables import ImageHTMxTable
from .forms import FormImage, CustomModelMultipleChoiceField
from admin.mixins import AdminView, AdminFormView, AdminUpdateView, AdminDeleteView


class AdminImageIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = ImageHTMxTable
    filterset_class = ImageFilter
    template_name = "admin/template/index.html"

    def get_queryset(self):
        return Image.objects.filter(
            Q(type=Image.DISTRIBUTION) | Q(type=Image.APPLICATION) | Q(type=Image.LBAAS), is_deleted=False
        )

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminImageCreateView(AdminFormView):
    template_name = "admin/template/create.html"
    form_class = FormImage
    success_url = reverse_lazy("admin_template_index")

    def form_valid(self, form):
        if form.cleaned_data["type"] == Image.LBAAS:
            if Image.objects.filter(type=Image.LBAAS, is_deleted=False).exists():
                form.add_error("type", "LBaaS already exists.")
                return self.form_invalid(form)
        form.save()
        return super().form_valid(form)


class AdminImageUpdateView(AdminUpdateView):
    template_name = "admin/template/update.html"
    template_name_suffix = "_form"
    model = Image
    success_url = reverse_lazy("admin_template_index")
    fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AdminImageUpdateView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            "name",
            "slug",
            "type",
            "description",
            "md5sum",
            "distribution",
            "arch",
            "file_name",
            InlineCheckboxes("regions", css_class="checkboxinput"),
            "is_active",
        )

    def get_form(self, form_class=None):
        form = super(AdminImageUpdateView, self).get_form(form_class)
        form.fields["regions"] = CustomModelMultipleChoiceField(
            queryset=Region.objects.filter(is_deleted=False), widget=forms.CheckboxSelectMultiple(), required=False
        )
        return form

    def get_context_data(self, **kwargs):
        context = super(AdminImageUpdateView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context


class AdminImageDeleteView(AdminDeleteView):
    template_name = "admin/template/delete.html"
    model = Image
    success_url = reverse_lazy("admin_template_index")

    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        image.delete()
        return super(self).delete(request, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(AdminImageDeleteView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_context_data(self, **kwargs):
        context = super(AdminImageDeleteView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context
