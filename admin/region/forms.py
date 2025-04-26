from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms

from region.models import Feature, Region


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    type_input = "checkbox"

    def label_from_instance(self, item):
        for choice in Feature.FEATURE_CHOICES:
            if item.name == choice[0]:
                return choice[1]
        return f"{item.name}"


class FormRegion(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormRegion, self).__init__(*args, **kwargs)
        self.fields["features"] = CustomModelMultipleChoiceField(
            queryset=Feature.objects.all(), widget=forms.CheckboxSelectMultiple(), required=False
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout("name", "slug", "description", InlineCheckboxes("features"))

    class Meta:
        model = Region
        fields = "__all__"
