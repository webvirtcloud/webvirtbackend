from django import forms
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from region.models import Region
from compute.models import Compute


class CustomModelChoiceField(forms.ModelChoiceField):
    type_input = "select"

    def label_from_instance(self, item):
        return f"{item.name}"


class FormCompute(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FormCompute, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["region"] = CustomModelChoiceField(
            queryset=Region.objects.filter(is_deleted=False)
        )
        self.fields["region"].empty_label = None

    class Meta:
        model = Compute
        fields = ["name", "arch", "description", "hostname", "token", "region"]


class FormStartAction(forms.Form):
    action = forms.ChoiceField(
        choices=[("start", "Start"), ("stop", "Stop")]
    )

    def __init__(self, *args, **kwargs):
        super(FormStartAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        if action not in ["start", "stop"]:
            raise forms.ValidationError("Invalid action")
        return cleaned_data


class FormAutostartAction(forms.Form):
    action = forms.ChoiceField(
        choices=[("autostart", "Autostart"), ("manualstart", "Manualstart")]
    )

    def __init__(self, *args, **kwargs):
        super(FormAutostartAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        if action not in ["autostart", "manualstart"]:
            raise forms.ValidationError("Invalid action")
        return cleaned_data


class FormVolumeCreateAction(forms.Form):
    name = forms.CharField(label="Name", max_length=100, validators=[RegexValidator("^[a-zA-Z0-9_-]+$")])
    size = forms.IntegerField(label="Size", min_value=1, initial=20)
    format = forms.ChoiceField(label="Formate", required=True, choices=(("raw", "raw"), ("qcow2", "qcow2")))

    def __init__(self, *args, **kwargs):
        super(FormVolumeCreateAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormVolumeCloneAction(forms.Form):
    action = forms.HiddenInput(attrs={"value": "clone"})
    name = forms.CharField(label="Name", max_length=100, validators=[RegexValidator("^[a-zA-Z0-9_-]+$")])

    def __init__(self, *args, **kwargs):
        super(FormVolumeCloneAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormVolumeResizeAction(forms.Form):
    action = forms.HiddenInput(attrs={"value": "resize"})
    size = forms.IntegerField(label="Size", min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super(FormVolumeResizeAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormNwfilterCreateAction(forms.Form):
    xml = forms.CharField(label="XML", widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        super(FormNwfilterCreateAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
