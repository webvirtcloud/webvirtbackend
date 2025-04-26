from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms

from region.models import Region
from size.models import Size


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    type_input = "checkbox"

    def label_from_instance(self, item):
        return f"{item.name}"


class FormSize(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSize, self).__init__(*args, **kwargs)
        self.fields["regions"] = CustomModelMultipleChoiceField(
            queryset=Region.objects.filter(is_deleted=False), widget=forms.CheckboxSelectMultiple(), required=False
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            "name",
            "slug",
            "description",
            "vcpu",
            "disk",
            "memory",
            "type",
            "transfer",
            "price",
            InlineCheckboxes("regions"),
        )

    class Meta:
        model = Size
        labels = {
            "disk": "Disk (Gb)",
            "price": "Price (Hourly)",
            "memory": "Memory (Mb)",
            "transfer": "Transfer (Tb)",
        }
        fields = "__all__"
