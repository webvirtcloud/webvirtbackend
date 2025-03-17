from django import forms
from crispy_forms.layout import Layout
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineCheckboxes

from size.models import Size, DBMS


MIN_MEMORY_SIZE = 2 * (1024**3)


class CustomModelChoiceField(forms.ModelChoiceField):
    type_input = "select"

    def label_from_instance(self, item):
        return (
            f"{item.description} - vCPU: {item.vcpu}, RAM: {item.memory//(1024**2)}Mb, Disk: {item.disk//(1024**3)}Gb"
        )


class FormDBMS(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDBMS, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.fields["engine"] = forms.ChoiceField(choices=DBMS.ENGINE_CHOICES)
        self.fields["sizes"] = CustomModelChoiceField(
            empty_label=None,
            queryset=Size.objects.filter(memory__gte=MIN_MEMORY_SIZE, type=Size.VIRTANCE, is_deleted=False),
        )
        self.helper.layout = Layout("name", "slug", "description", "engine", "version", InlineCheckboxes("sizes"))

    class Meta:
        model = DBMS
        labels = {"sizes": "Available for Sizes"}
        fields = "__all__"
