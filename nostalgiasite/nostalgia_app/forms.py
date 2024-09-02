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
    want_notification = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=True,
        label="Do you want to be notified of the decision?"
    )
    notification_preference = forms.ChoiceField(
        choices=[('email', 'Email'), ('phone', 'Phone')],
        widget=forms.RadioSelect,
        required=False,
        label="How would you like to be notified?"
    )
    description = forms.CharField(widget=forms.Textarea, min_length=1)

    class Meta:
        model = UserSubmittedFact
        fields = ['year', 'title', 'description', 'categories', 'source_url', 'want_notification', 'notification_preference', 'notification_email', 'notification_phone']
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notification_email'].required = False
        self.fields['notification_phone'].required = False

    def clean(self):
        cleaned_data = super().clean()
        want_notification = cleaned_data.get('want_notification')
        notification_preference = cleaned_data.get('notification_preference')
        email = cleaned_data.get('notification_email')
        phone = cleaned_data.get('notification_phone')

        if want_notification == 'yes':
            if not notification_preference:
                raise forms.ValidationError("Please select a notification preference.")
            if notification_preference == 'email' and not email:
                raise forms.ValidationError("Please provide an email for notifications.")
            elif notification_preference == 'phone' and not phone:
                raise forms.ValidationError("Please provide a phone number for notifications.")
        else:
            # If user doesn't want notifications, clear these fields
            cleaned_data['notification_preference'] = None
            cleaned_data['notification_email'] = None
            cleaned_data['notification_phone'] = None

        return cleaned_data

class FactReviewForm(forms.ModelForm):
    class Meta:
        model = UserSubmittedFact
        fields = ['status', 'review_notes']
        widgets = {
            'review_notes': forms.Textarea(attrs={'rows': 4}),
        }