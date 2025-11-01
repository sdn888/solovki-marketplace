from django.db import models


class Route(models.Model):
    THEME_CHOICES = [
        ('historical', 'Исторический'),
        ('religious', 'Религиозный'),
        ('nature', 'Природоведческий'),
        ('mixed', 'Смешанный'),
    ]

    TRANSPORT_CHOICES = [
        ('foot', 'Пеший'),
        ('bike', 'Велосипед'),
        ('car', 'Автомобиль'),
        ('boat', 'Лодка'),
        ('mixed', 'Смешанный'),
    ]

    # Основная информация
    title = models.CharField(max_length=200, verbose_name="Название маршрута")
    description = models.TextField(verbose_name="Описание")
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, verbose_name="Тематика")
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, verbose_name="Тип транспорта")
    duration_hours = models.FloatField(verbose_name="Длительность (часов)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    need_food_supply = models.BooleanField(default=False, verbose_name="Нужен запас еды")
    max_participants = models.IntegerField(default=10, verbose_name="Максимум участников")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    # Геоданные маршрута
    start_lat = models.FloatField(verbose_name="Широта старта", null=True, blank=True)
    start_lon = models.FloatField(verbose_name="Долгота старта", null=True, blank=True)
    end_lat = models.FloatField(verbose_name="Широта финиша", null=True, blank=True)
    end_lon = models.FloatField(verbose_name="Долгота финиша", null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"


class Waypoint(models.Model):
    WAYPOINT_TYPES = [
        ('attraction', 'Достопримечательность'),
        ('food', 'Точка питания'),
        ('info', 'Информационная точка'),
        ('view', 'Смотровая площадка'),
        ('start', 'Старт'),
        ('end', 'Финиш'),
        ('break', 'Место отдыха'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='waypoints')
    name = models.CharField(max_length=200, verbose_name="Название точки")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(verbose_name="Порядковый номер в маршруте")
    waypoint_type = models.CharField(max_length=20, choices=WAYPOINT_TYPES, verbose_name="Тип точки")

    # Геоданные точки
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")

    # Дополнительная информация
    estimated_stay_minutes = models.IntegerField(default=0, verbose_name="Время на посещение (минут)")
    has_food = models.BooleanField(default=False, verbose_name="Есть питание")
    has_toilets = models.BooleanField(default=False, verbose_name="Есть туалеты")
    is_optional = models.BooleanField(default=False, verbose_name="Опциональная точка")

    def __str__(self):
        return f"{self.order}. {self.name} ({self.get_waypoint_type_display()})"

    class Meta:
        ordering = ['route', 'order']
        verbose_name = "Точка маршрута"
        verbose_name_plural = "Точки маршрута"
        unique_together = ['route', 'order']