from django import forms
from django.core.validators import validate_slug
from size.models import Size


class FormSize(forms.ModelForm):

    class Meta:
        model = Size
        fields = ("name", "slug", "description", "vcpu", "disk", "memory", "transfer", "regions", "price")
