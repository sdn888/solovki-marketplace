from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name="Роль"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    def is_manager(self):
        return self.role in ['manager', 'admin']

    def is_admin(self):
        return self.role == 'admin'

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    # ИЗБРАННЫЕ ТОЧКИ
    favorite_waypoints = models.ManyToManyField(
        'Waypoint',
        through='FavoriteWaypoint',
        related_name='favorited_by',
        blank=True
    )
