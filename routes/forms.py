from django import forms
from .models import Route, Waypoint


class CoordinateFloatField(forms.FloatField):
    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace(',', '.')
        return super().to_python(value)


class WaypointForm(forms.ModelForm):
    latitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0245'})
    )
    longitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105'})
    )

    class Meta:
        model = Waypoint
        fields = '__all__'
        widgets = {
            'short_description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Краткое описание, которое будет показываться в списках и карточках'
            }),
            'detailed_description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Полное и подробное описание достопримечательности'
            }),
            'history_info': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Исторические факты, даты, значимые события'
            }),
            'architecture_info': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Архитектурные особенности, стиль, материалы'
            }),
            'visit_notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Особенности посещения, рекомендации, что учесть'
            }),
            'path_description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Как добраться, описание пути, ориентиры'
            }),
            'best_time_to_visit': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Лучшее время года, время суток, погодные условия'
            }),
        }
        help_texts = {
            'short_description': 'Отображается в карточках и списках (до 1000 символов)',
            'detailed_description': 'Полное описание для страницы точки маршрута',
            'latitude': 'Широта в формате 64.0245',
            'longitude': 'Долгота в формате 35.7105',
        }


class RouteForm(forms.ModelForm):
    start_lat = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0345'})
    )
    start_lon = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105'})
    )
    end_lat = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0345'})
    )
    end_lon = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105'})
    )

    class Meta:
        model = Route
        fields = '__all__'
        help_texts = {
            'start_lat': 'Широта начала маршрута (отель "Морюшко")',
            'start_lon': 'Долгота начала маршрута',
        }