from django import forms
from django.core.validators import validate_slug
from region.models import Region


class FormRegion(forms.ModelForm):

    class Meta:
        model = Region
        fields = ("name", "slug", "description")
