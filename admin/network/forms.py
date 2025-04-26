from ipaddress import ip_address, ip_network

from crispy_forms.helper import FormHelper
from django import forms

from network.models import Network
from region.models import Region


class CustomModelChoiceField(forms.ModelChoiceField):
    type_input = "select"

    def label_from_instance(self, item):
        return f"{item.name}"


class FormNetwork(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormNetwork, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["region"] = CustomModelChoiceField(queryset=Region.objects.filter(is_deleted=False))
        self.fields["region"].empty_label = None

    class Meta:
        model = Network
        fields = ["cidr", "netmask", "dns1", "dns2", "type", "region"]

    def clean(self):
        cidr = self.cleaned_data.get("cidr")
        netmask = self.cleaned_data.get("netmask")
        dns1 = self.cleaned_data.get("dns1")
        dns2 = self.cleaned_data.get("dns2")
        region = self.cleaned_data.get("region")
        net_type = self.cleaned_data.get("type")

        # Validate CIDR
        try:
            ip_network(f"{cidr}/{netmask}")
        except ValueError as err:
            raise forms.ValidationError(err)

        # Check if CIDR already exists
        if Network.objects.filter(cidr=cidr, netmask=netmask, region=region, is_deleted=True).exists():
            raise forms.ValidationError("Network already exists in this region")

        # Check if CIDR compute already exists in the region
        if net_type == Network.COMPUTE:
            if cidr != "10.255.0.0" and netmask != "255.255.0.0":
                raise forms.ValidationError("Compute network must be '10.255.0.0/255.255.0.0'")

        # Validate DNS
        if net_type == Network.PUBLIC:
            if not dns1 or not dns2:
                raise forms.ValidationError("DNS1 and DNS2 are required for public network")
            if dns1 == dns2:
                raise forms.ValidationError("DNS1 and DNS2 cannot be the same")
            if dns1 == "0.0.0.0" and dns2 == "0.0.0.0":
                raise forms.ValidationError("DNS1 and DNS2 cannot be 0.0.0.0")
            try:
                ip_address(dns1)
                ip_address(dns2)
            except ValueError as err:
                raise forms.ValidationError(err)

        return self.cleaned_data

    def save(self, commit=True):
        cidr = self.cleaned_data.get("cidr")
        netmask = self.cleaned_data.get("netmask")
        dns1 = self.cleaned_data.get("dns1")
        dns2 = self.cleaned_data.get("dns2")
        region = self.cleaned_data.get("region")
        net_type = self.cleaned_data.get("type")
        subnet = ip_network(f"{cidr}/{netmask}")

        network = Network.objects.create(
            cidr=cidr,
            netmask=netmask,
            gateway=str(subnet[1]),
            type=net_type,
            version=subnet.version,
            dns1=dns1,
            dns2=dns2,
            region=region,
        )

        return network
