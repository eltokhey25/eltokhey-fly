"""
core/forms.py
Public form definitions. Only the review form is public; the booking
form is validated by hand in core/views.booking.
"""
from django import forms

from .models import REVIEW_COUNTRIES, Review


class ReviewForm(forms.ModelForm):
    """Public "share your experience" form used by core.views.review_submit.

    Adds two things to the plain ModelForm:
        * `rating` becomes a hidden 1-5 field driven by the star widget in
          review_submit.html, so the value is still a real, validated integer
        * `website`, an invisible honeypot field that rejects naive bots
    """

    rating = forms.TypedChoiceField(
        label='تقييمك',
        required=True,
        coerce=int,
        choices=[(n, f'{n}') for n in range(1, 6)],
        error_messages={'required': 'من فضلك اختر تقييمك (1 إلى 5 نجوم).'},
        widget=forms.HiddenInput(attrs={'id': 'id_rating'}),
    )

    class Meta:
        """Public review form: the fields a customer actually fills in."""
        model = Review
        fields = ['name', 'country', 'photo', 'rating', 'text', 'trip']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'مثال: محمد أحمد',
                'autocomplete': 'name',
            }),
            'country': forms.Select(attrs={'class': 'input'}),
            'photo': forms.FileInput(attrs={
                'class': 'input',
                'accept': 'image/*',
            }),
            'text': forms.Textarea(attrs={
                'class': 'input textarea',
                'rows': 5,
                'placeholder': 'شاركنا تجربتك مع رحلاتنا…',
            }),
            'trip': forms.Select(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        """Apply Arabic labels and narrow the trip/country choices.

        Args:
            *args: Positional args forwarded to forms.ModelForm.
            **kwargs: Keyword args forwarded to forms.ModelForm.
        """
        super().__init__(*args, **kwargs)
        labels = {
            'name': 'اسمك',
            'country': 'دولتك',
            'photo': 'صورتك (اختياري)',
            'rating': 'تقييمك',
            'text': 'رأيك في الرحلة',
            'trip': 'الرحلة التي سافرت معها (اختياري)',
        }
        for name, label in labels.items():
            self.fields[name].label = label
        # Arabic country list lives in the model so the dashboard can reuse it.
        self.fields['country'].choices = REVIEW_COUNTRIES
        # A review can only reference a trip that is still public.
        self.fields['trip'].queryset = self.fields['trip'].queryset.filter(is_active=True)
        self.fields['trip'].empty_label = '———'
        self.fields['trip'].required = False

    # Honeypot: hidden from humans, irresistible to bots. Any value fails
    # validation in clean_website below.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'hp-field',
            'autocomplete': 'off',
            'tabindex': '-1',
        }),
        label='',
    )

    def clean_website(self):
        """Reject the submission when the honeypot field was filled in.

        Returns:
            str: The cleaned (always empty) value.

        Raises:
            forms.ValidationError: When a bot filled the hidden field.
        """
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError('تم رفض الإرسال.')
        return value