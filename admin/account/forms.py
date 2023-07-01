from django import forms
from crispy_forms.helper import FormHelper


class FormChangePasswordAdmin(forms.Form):
    old_password = forms.CharField(
        label=("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'old-password'}),
    )
    new_password1 = forms.CharField(
        label=("New password"),
        min_length=8,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password2'}),
    )
    new_password2 = forms.CharField(
        label=("Confim password"),
        min_length=8,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password2'}),
    )

    def __init__(self, user, *args, **kwargs):
        super(FormChangePasswordAdmin, self).__init__(*args, **kwargs)
        self.user = user
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        # Check if the old password matches the user's current password
        if old_password and not self.user.check_password(old_password):
            raise forms.ValidationError("Incorrect old password.")

        # Check if the new passwords match
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("New password and confirm password do not match.")
        
        return cleaned_data

    def save(self, *args, **kwargs):
        new_password1 = self.cleaned_data.get("new_password1")
        self.user.set_password(new_password1)
        self.user.save()
        return self.user
