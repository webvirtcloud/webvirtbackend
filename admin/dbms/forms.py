from django import forms
from django.conf import settings
from crispy_forms.layout import Layout
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineCheckboxes

from size.models import Size, DBMS


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    type_input = "checkbox"

    def label_from_instance(self, item):
        return f"{item.description} (Mem: {item.memory//(1024**3)}Gb)"


class FormDBMS(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormDBMS, self).__init__(*args, **kwargs)
        self.fields["engine"] = forms.ChoiceField(choices=DBMS.ENGINE_CHOICES)
        self.fields["sizes"] = CustomModelMultipleChoiceField(
            required=False,
            label="Available for Sizes",
            widget=forms.CheckboxSelectMultiple(),
            queryset=Size.objects.filter(
                memory__gte=settings.DBASS_MIN_VM_MEM_SIZE, type=Size.VIRTANCE, is_deleted=False
            ),
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout("name", "slug", "description", "engine", "version", InlineCheckboxes("sizes"))

    class Meta:
        model = DBMS
        fields = "__all__"
