from django import forms
from .models import Route, Waypoint


class CoordinateFloatField(forms.FloatField):
    def to_python(self, value):
        if value is None:
            return None
        # Заменяем запятую на точку
        if isinstance(value, str):
            value = value.replace(',', '.')
        return super().to_python(value)


class WaypointForm(forms.ModelForm):
    latitude = CoordinateFloatField()
    longitude = CoordinateFloatField()

    class Meta:
        model = Waypoint
        fields = '__all__'
        widgets = {
            'short_description': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Краткое описание точки для карточек и списков'}),
            'detailed_description': forms.Textarea(
                attrs={'rows': 6, 'placeholder': 'Подробное описание достопримечательности'}),
            'history_info': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Историческая справка'}),
            'architecture_info': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Архитектурные особенности'}),
            'visit_notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Особенности посещения, рекомендации'}),
            'path_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Описание пути до точки'}),
            'best_time_to_visit': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Лучшее время для посещения'}),
        }


class RouteForm(forms.ModelForm):
    start_lat = CoordinateFloatField(required=False)
    start_lon = CoordinateFloatField(required=False)
    end_lat = CoordinateFloatField(required=False)
    end_lon = CoordinateFloatField(required=False)

    class Meta:
        model = Route
        fields = '__all__'