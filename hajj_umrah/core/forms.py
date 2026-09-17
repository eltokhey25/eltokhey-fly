from django import forms

from .models import REVIEW_COUNTRIES, Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label='تقييمك',
        required=True,
        coerce=int,
        choices=[(n, f'{n}') for n in range(1, 6)],
        error_messages={'required': 'من فضلك اختر تقييمك (1 إلى 5 نجوم).'},
        widget=forms.HiddenInput(attrs={'id': 'id_rating'}),
    )

    class Meta:
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
        self.fields['country'].choices = REVIEW_COUNTRIES
        self.fields['trip'].queryset = self.fields['trip'].queryset.filter(is_active=True)
        self.fields['trip'].empty_label = '———'
        self.fields['trip'].required = False

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
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError('تم رفض الإرسال.')
        return value