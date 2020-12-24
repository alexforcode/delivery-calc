from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import Tab, TabHolder, FormActions
from crispy_forms.layout import Layout, Submit, Field, Row


class CalculatorForm(forms.Form):
    derival_city = forms.CharField(
        label='Откуда',
        max_length=100
    )
    arrival_city = forms.CharField(
        label='Куда',
        max_length=100
    )
    derival_region = forms.CharField(
        max_length=100,
        required=False
    )
    arrival_region = forms.CharField(
        max_length=100,
        required=False
    )
    width = forms.FloatField(
        label='Ширина',
        min_value=0,
        max_value=9999,
        required=False,
        localize=True,
        widget=forms.TextInput()
    )
    height = forms.FloatField(
        label='Высота',
        min_value=0,
        max_value=9999,
        required=False,
        localize=True,
        widget=forms.TextInput()
    )
    length = forms.FloatField(
        label='Длина',
        min_value=0,
        max_value=9999,
        required=False,
        localize=True,
        widget=forms.TextInput()
    )
    volume = forms.FloatField(
        label='Объём',
        min_value=0,
        max_value=9999,
        required=False,
        localize=True,
        widget=forms.TextInput()
    )
    weight = forms.FloatField(
        label='Вес',
        min_value=0,
        max_value=99999,
        localize=True,
        widget=forms.TextInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Field('derival_city', wrapper_class='col-md-6', placeholder='Город'),
                Field('arrival_city', wrapper_class='col-md-6', placeholder='Город'),
            ),
            Row(
                Field('derival_region', wrapper_class='col-md-6', placeholder='Регион', id='derival_region'),
                Field('arrival_region', wrapper_class='col-md-6', placeholder='Регион', id='arrival_region'),
            ),
            Row(
                Field('weight', wrapper_class='col-md-4'),
            ),
            TabHolder(
                Tab(
                    'Объём',
                    Row(
                        Field('volume', wrapper_class='col-md-4'),
                    ),
                    css_id='vols',
                ),
                Tab(
                    'Размеры',
                    Row(
                        Field('width', wrapper_class='col-md-4'),
                        Field('height', wrapper_class='col-md-4'),
                        Field('length', wrapper_class='col-md-4'),
                    ),
                    css_id='dims',
                ),
            ),
            FormActions(
                Submit('submit', 'Рассчитать')
            )
        )
        self.fields['derival_region'].label = False
        self.fields['arrival_region'].label = False

    def clean(self):
        cleaned_data = super().clean()
        width = cleaned_data.get('width')
        length = cleaned_data.get('length')
        height = cleaned_data.get('height')
        volume = cleaned_data.get('volume')

        if not volume:
            if not width or not length or not height:
                raise ValidationError('Заполните размеры (ширина, высота, длина) и/или объём груза.')
