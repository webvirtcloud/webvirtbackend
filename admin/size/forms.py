from django import forms
from django.core.validators import validate_slug
from size.models import Size
from region.models import Region


class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):    
    def label_from_instance(self, item):
        return f"{item.name}"


class FormSize(forms.ModelForm):

    class Meta:
        model = Size
        fields = ["name", "slug", "description", "vcpu", "disk", "memory", "transfer", "regions", "price"]

    def __init__(self, *args, **kwargs):
        super(FormSize, self).__init__(*args, **kwargs)
        self.fields["regions"] = CustomModelMultipleChoiceField(
            queryset=Region.objects.filter(is_deleted=False), 
            widget=forms.CheckboxSelectMultiple()
        )
