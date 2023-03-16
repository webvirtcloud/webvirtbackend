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


class FormStorageDirCreate(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"value": "images"}),
        validators=[RegexValidator("^[a-z0-9]+$")],
    )
    type = forms.HiddenInput(attrs={"value": "dir"})
    target = forms.CharField(
        max_length=250,
        widget=forms.TextInput(attrs={"value": "/var/lib/libvirt/images"}),
        validators=[RegexValidator("^[a-zA-Z0-9/]+$")],
    )

    def __init__(self, *args, **kwargs):
        super(FormStorageDirCreate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormStorageRBDCreate(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"value": "volumes"}),
        validators=[RegexValidator("^[a-z0-9]+$")],
    )
    type = forms.HiddenInput(attrs={"value": "rbd"})
    user = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"value": "libvirt"}))
    host1 = forms.CharField(max_length=100,widget=forms.TextInput(attrs={"value": "192.168.0.1"}))
    host2 = forms.CharField(max_length=100, required=False)
    host3 = forms.CharField(max_length=100, required=False)
    pool = forms.CharField(max_length=50, widget=forms.TextInput(attrs={"value": "volumes"}))
    secret = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super(FormStorageRBDCreate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormVolumeCreateAction(forms.Form):
    name = forms.CharField(max_length=100, validators=[RegexValidator("^[a-zA-Z0-9_-]+$")])
    size = forms.IntegerField(min_value=1, initial=20)
    format = forms.ChoiceField(choices=(("raw", "raw"), ("qcow2", "qcow2")))

    def __init__(self, *args, **kwargs):
        super(FormVolumeCreateAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormVolumeCloneAction(forms.Form):
    action = forms.HiddenInput(attrs={"value": "clone"})
    name = forms.CharField(max_length=100, validators=[RegexValidator("^[a-zA-Z0-9_-]+$")])

    def __init__(self, *args, **kwargs):
        super(FormVolumeCloneAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormVolumeResizeAction(forms.Form):
    action = forms.HiddenInput(attrs={"value": "resize"})
    size = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super(FormVolumeResizeAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormNetworkCreate(forms.Form):
    name = forms.CharField(max_length=100, validators=[RegexValidator("^[a-zA-Z0-9_-]+$")])
    forward = forms.HiddenInput(attrs={"value": "bridge"})
    bridge_name = forms.ChoiceField(label="Bridge Interface", choices=[])
    openvswitch = forms.BooleanField(label="Open vSwitch", required=False)

    def __init__(self, *args, **kwargs):
        super(FormNetworkCreate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormSecretCreateAction(forms.Form):
    ephemeral = forms.ChoiceField(choices=(("no", "no"), ("yes", "yes")))
    private = forms.ChoiceField(choices=(("no", "no"), ("yes", "yes")))
    type = forms.ChoiceField(choices=(("ceph", "ceph"), ("volume", "volume"), ("iscsi", "iscsi")))
    data = forms.CharField(
        max_length=100,
        initial="client.libvirt",
        validators=[RegexValidator("^[0-9a-z.]+$")],
    )

    def __init__(self, *args, **kwargs):
        super(FormSecretCreateAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormSecretValueAction(forms.Form):
    value = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super(FormSecretValueAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class FormNwfilterCreateAction(forms.Form):
    xml = forms.CharField(label="XML", widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(FormNwfilterCreateAction, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
