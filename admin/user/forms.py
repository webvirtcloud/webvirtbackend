from django import forms
from crispy_forms.helper import FormHelper

from account.models import User


class FormUser(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormUser, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["password"].widget = forms.PasswordInput()
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")

        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        return cleaned_data

    def save(self, *args, **kwargs):
        User.objects.create(
            is_admin=False,
            is_active=True,
            is_verified=True,
            is_email_verified=True,
            email=self.cleaned_data.get("email"),
            password=self.cleaned_data.get("password"),
            first_name=self.cleaned_data.get("first_name"),
            last_name=self.cleaned_data.get("last_name"),
        )