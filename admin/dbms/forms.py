from django import forms
from crispy_forms.helper import FormHelper

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
        self.fields["required_size"] = CustomModelChoiceField(
            queryset=Size.objects.filter(memory__gte=MIN_MEMORY_SIZE, is_deleted=False),
            empty_label=None,
        )

    class Meta:
        model = DBMS
        labels = {"required_size": "Minimal Required Size"}
        fields = ("name", "slug", "description", "engine", "version", "required_size")
