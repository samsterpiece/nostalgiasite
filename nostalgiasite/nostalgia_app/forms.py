from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserSubmittedFact, Category

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class FactSubmissionForm(forms.ModelForm):
    notification_preference = forms.ChoiceField(
        choices=[('email', 'Email'), ('phone', 'Phone')],
        widget=forms.RadioSelect,
        required=True
    )
    description = forms.CharField(widget=forms.Textarea, min_length=1)


    class Meta:
        model = UserSubmittedFact
        fields = ['year', 'title', 'description', 'categories', 'source_url', 'notification_email', 'notification_phone']
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        notification_preference = cleaned_data.get('notification_preference')
        email = cleaned_data.get('notification_email')
        phone = cleaned_data.get('notification_phone')

        if notification_preference == 'email' and not email:
            raise forms.ValidationError("Please provide an email for notifications.")
        elif notification_preference == 'phone' and not phone:
            raise forms.ValidationError("Please provide a phone number for notifications.")

        return cleaned_data
    


class FactReviewForm(forms.ModelForm):
    class Meta:
        model = UserSubmittedFact
        fields = ['status', 'review_notes']
        widgets = {
            'review_notes': forms.Textarea(attrs={'rows': 4}),
        }