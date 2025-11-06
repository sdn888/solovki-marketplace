import os
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponse
from .models import Route, Waypoint, FavoriteWaypoint, CustomUser, PersonalRoute, PersonalRoutePoint, VisitNote
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView, ListView, CreateView, DeleteView, DetailView
from .mixins import ManagerRequiredMixin, AdminRequiredMixin
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .export_utils import PDFExporter, GPXExporter, SimplePDFExporter
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from django.db.models import Count, Avg, Q
from collections import Counter



def route_list(request):
    routes = Route.objects.filter(is_active=True).prefetch_related('tips', 'waypoints')
    return render(request, 'routes/route_list.html', {'routes': routes})

def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk, is_active=True)
    waypoints = route.waypoints.all().order_by('order').prefetch_related('images')
    tips = route.tips.all().order_by('order')
    return render(request, 'routes/route_detail.html', {
        'route': route,
        'waypoints': waypoints,
        'tips': tips
    })

def route_geojson(request, pk):
    route = get_object_or_404(Route, pk=pk)
    waypoints = route.waypoints.all().order_by('order')

    features = []

    # Добавляем точки маршрута
    for waypoint in waypoints:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [waypoint.longitude, waypoint.latitude]
            },
            "properties": {
                "name": waypoint.name,
                "type": waypoint.waypoint_type,
                "order": waypoint.order,
                "description": waypoint.description,
                "stay_minutes": waypoint.estimated_stay_minutes
            }
        })

    # Добавляем линию маршрута (если есть координаты)
    if waypoints.count() > 1:
        coordinates = [[wp.longitude, wp.latitude] for wp in waypoints]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "name": f"Маршрут: {route.title}",
                "color": "#3388ff",
                "weight": 4
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(geojson)


@login_required
@require_POST
def toggle_favorite_waypoint(request, waypoint_id):
    """Добавить/удалить точку в избранное"""
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    favorite, created = FavoriteWaypoint.objects.get_or_create(
        user=request.user,
        waypoint=waypoint
    )

    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed', 'is_favorite': False})

    return JsonResponse({'status': 'added', 'is_favorite': True})


@login_required
def favorite_waypoints_map(request):
    """Карта с избранными точками пользователя"""
    favorite_waypoints = Waypoint.objects.filter(favorited_by=request.user)

    return render(request, 'routes/favorite_waypoints_map.html', {
        'favorite_waypoints': favorite_waypoints,
        'page_title': 'Мои избранные точки'
    })


@login_required
def favorite_waypoints_list(request):
    """Список избранных точек пользователя"""
    favorite_waypoints = Waypoint.objects.filter(favorited_by=request.user)

    return render(request, 'routes/favorite_waypoints_list.html', {
        'favorite_waypoints': favorite_waypoints,
        'page_title': 'Мои избранные точки'
    })

class CustomLoginView(LoginView):
    template_name = 'routes/login.html'


class CustomLogoutView(LogoutView):
    next_page = '/'


class ProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'routes/profile.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
    success_url = '/profile/'

    def get_object(self):
        return self.request.user


class ManagerDashboardView(ManagerRequiredMixin, TemplateView):
    template_name = 'routes/manager_dashboard.html'


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'routes/admin_dashboard.html'


# ПЕРСОНАЛЬНЫЕ МАРШРУТЫ
class PersonalRouteListView(LoginRequiredMixin, ListView):
    model = PersonalRoute
    template_name = 'routes/personal_routes_list.html'
    context_object_name = 'personal_routes'

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)


class PersonalRouteCreateView(LoginRequiredMixin, CreateView):
    model = PersonalRoute
    template_name = 'routes/personal_route_form.html'
    fields = ['name', 'description', 'is_public', 'color']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('personal_route_detail', kwargs={'pk': self.object.pk})


class PersonalRouteUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalRoute
    template_name = 'routes/personal_route_form.html'
    fields = ['name', 'description', 'is_public', 'color']

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('personal_route_detail', kwargs={'pk': self.object.pk})


class PersonalRouteDeleteView(LoginRequiredMixin, DeleteView):
    model = PersonalRoute
    template_name = 'routes/personal_route_confirm_delete.html'

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('personal_routes_list')


class PersonalRouteDetailView(LoginRequiredMixin, DetailView):
    model = PersonalRoute
    template_name = 'routes/personal_route_detail.html'
    context_object_name = 'personal_route'

    def get_queryset(self):
        return PersonalRoute.objects.filter(user=self.request.user)


@login_required
@require_POST
def add_point_to_personal_route(request, route_id, waypoint_id):
    """Добавить точку в персональный маршрут"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)

    # Определяем следующий порядковый номер
    next_order = personal_route.points.count() + 1

    PersonalRoutePoint.objects.create(
        personal_route=personal_route,
        waypoint=waypoint,
        order=next_order
    )

    return JsonResponse({'status': 'success', 'order': next_order})


@login_required
@require_POST
def remove_point_from_personal_route(request, route_id, point_id):
    """Удалить точку из персонального маршрута"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    point = get_object_or_404(PersonalRoutePoint, id=point_id, personal_route=personal_route)

    point.delete()

    # Обновляем порядок оставшихся точек
    points = personal_route.points.all().order_by('order')
    for index, point in enumerate(points, 1):
        point.order = index
        point.save()

    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def update_personal_route_points_order(request, route_id):
    """Обновить порядок точек в маршруте"""
    personal_route = get_object_or_404(PersonalRoute, id=route_id, user=request.user)
    new_order = request.POST.getlist('order[]')

    for index, point_id in enumerate(new_order, 1):
        point = PersonalRoutePoint.objects.get(id=point_id, personal_route=personal_route)
        point.order = index
        point.save()

    return JsonResponse({'status': 'success'})


# ЗАМЕТКИ О ПОСЕЩЕНИЯХ
class VisitNoteCreateView(LoginRequiredMixin, CreateView):
    model = VisitNote
    template_name = 'routes/visit_note_form.html'
    fields = ['waypoint', 'visited_date', 'rating', 'notes', 'photos']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('favorite_waypoints_list')


class VisitNoteUpdateView(LoginRequiredMixin, UpdateView):
    model = VisitNote
    template_name = 'routes/visit_note_form.html'
    fields = ['visited_date', 'rating', 'notes', 'photos']

    def get_queryset(self):
        return VisitNote.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('favorite_waypoints_list')


@login_required
@require_POST
def update_favorite_notes(request, waypoint_id):
    """Обновить заметки для избранной точки"""
    favorite = get_object_or_404(FavoriteWaypoint, waypoint_id=waypoint_id, user=request.user)
    notes = request.POST.get('notes', '')
    planned_visit_date = request.POST.get('planned_visit_date', '')
    priority = request.POST.get('priority', 1)

    favorite.notes = notes
    favorite.priority = priority
    if planned_visit_date:
        favorite.planned_visit_date = planned_visit_date
    favorite.save()

    return JsonResponse({'status': 'success'})


@login_required
def export_personal_route(request, pk, format_type):
    personal_route = get_object_or_404(PersonalRoute, pk=pk, user=request.user)

    if format_type == 'pdf':
        exporter = PDFExporter(personal_route)
        filepath = exporter.export_to_pdf()
    elif format_type == 'gpx':
        exporter = GPXExporter(personal_route)
        filepath = exporter.export_to_gpx()
    elif format_type == 'simple_pdf':
        exporter = SimplePDFExporter(personal_route)
        filepath = exporter.export_simple_pdf()
    else:
        return HttpResponse("Неверный формат экспорта", status=400)

    # Создаем запись об экспорте
    export_format, created = ExportFormat.objects.get_or_create(
        format_type=format_type,
        defaults={'name': format_type.upper()}
    )

    route_export = RouteExport.objects.create(
        personal_route=personal_route,
        export_format=export_format
    )

    filename = os.path.basename(filepath)

    response = FileResponse(open(filepath, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
def export_personal_route_options(request, pk):
    personal_route = get_object_or_404(PersonalRoute, pk=pk, user=request.user)

    return render(request, 'routes/export_options.html', {
        'personal_route': personal_route,
        'export_formats': [
            {'type': 'pdf', 'name': 'PDF документ', 'description': 'Подробный маршрут с описанием точек'},
            {'type': 'simple_pdf', 'name': 'Простой PDF', 'description': 'Компактная версия для печати'},
            {'type': 'gpx', 'name': 'GPX файл', 'description': 'Для навигационных программ и устройств'},
        ]
    })


@login_required
def create_route_sharing(request, pk):
    personal_route = get_object_or_404(PersonalRoute, pk=pk, user=request.user)

    if request.method == 'POST':
        permission = request.POST.get('permission', 'view')
        expires_days = request.POST.get('expires_days', 30)
        password = request.POST.get('password', '')

        expires_at = timezone.now() + timedelta(days=int(expires_days))

        sharing = RouteSharing.objects.create(
            personal_route=personal_route,
            created_by=request.user,
            permission=permission,
            expires_at=expires_at,
            password=password if password else None
        )

        share_url = request.build_absolute_uri(
            reverse('view_shared_route', kwargs={'token': sharing.token})
        )

        return JsonResponse({
            'status': 'success',
            'share_url': share_url,
            'token': sharing.token
        })

    return render(request, 'routes/create_sharing.html', {
        'personal_route': personal_route
    })


def view_shared_route(request, token):
    sharing = get_object_or_404(RouteSharing, token=token, is_active=True)

    if sharing.is_expired():
        return render(request, 'routes/sharing_expired.html')

    # Проверка пароля если установлен
    if sharing.password:
        if request.method == 'POST':
            if request.POST.get('password') == sharing.password:
                request.session[f'sharing_access_{token}'] = True
            else:
                return render(request, 'routes/sharing_password.html', {
                    'error': 'Неверный пароль',
                    'token': token
                })
        elif not request.session.get(f'sharing_access_{token}'):
            return render(request, 'routes/sharing_password.html', {'token': token})

    personal_route = sharing.personal_route

    # Логируем просмотр
    sharing.download_count += 1
    sharing.save()

    can_edit = sharing.permission == 'edit'
    can_comment = sharing.permission in ['comment', 'edit']

    return render(request, 'routes/shared_route_detail.html', {
        'personal_route': personal_route,
        'sharing': sharing,
        'can_edit': can_edit,
        'can_comment': can_comment,
        'is_shared': True
    })


@login_required
def add_collaborator(request, pk):
    personal_route = get_object_or_404(PersonalRoute, pk=pk, user=request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        permission = request.POST.get('permission', 'view')

        try:
            user = CustomUser.objects.get(username=username)

            if user == request.user:
                return JsonResponse({'status': 'error', 'message': 'Нельзя добавить себя'})

            collaborator, created = RouteCollaborator.objects.get_or_create(
                personal_route=personal_route,
                user=user,
                defaults={
                    'permission': permission,
                    'added_by': request.user
                }
            )

            if not created:
                collaborator.permission = permission
                collaborator.save()

            return JsonResponse({'status': 'success', 'message': 'Соавтор добавлен'})

        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Пользователь не найден'})

    return JsonResponse({'status': 'error', 'message': 'Неверный запрос'})


@login_required
@require_POST
def add_route_comment(request, pk):
    personal_route = get_object_or_404(PersonalRoute, pk=pk)

    # Проверяем права на комментарии
    can_comment = False

    if personal_route.user == request.user:
        can_comment = True
    else:
        collaborator = RouteCollaborator.objects.filter(
            personal_route=personal_route,
            user=request.user,
            permission__in=['comment', 'edit']
        ).first()
        can_comment = bool(collaborator)

    if not can_comment:
        return JsonResponse({'status': 'error', 'message': 'Нет прав для комментариев'})

    comment_text = request.POST.get('comment', '').strip()

    if comment_text:
        RouteComment.objects.create(
            personal_route=personal_route,
            user=request.user,
            comment=comment_text
        )

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Комментарий не может быть пустым'})


@login_required
def visit_calendar(request, year=None, month=None):
    # Определяем текущий год и месяц если не указаны
    today = timezone.now().date()
    if not year or not month:
        year, month = today.year, today.month

    year, month = int(year), int(month)

    # Создаем календарь
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    # Получаем события для этого месяца
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    # Запланированные посещения
    planned_visits = FavoriteWaypoint.objects.filter(
        user=request.user,
        planned_visit_date__isnull=False,
        planned_visit_date__gte=start_date,
        planned_visit_date__lt=end_date
    ).select_related('waypoint')

    # Совершенные посещения
    actual_visits = VisitNote.objects.filter(
        user=request.user,
        visited_date__gte=start_date,
        visited_date__lt=end_date
    ).select_related('waypoint')

    # Группируем события по дням
    events_by_date = {}

    for visit in planned_visits:
        date_str = visit.planned_visit_date.isoformat()
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'type': 'planned',
            'waypoint': visit.waypoint,
            'favorite': visit,
            'time': visit.planned_visit_date
        })

    for visit in actual_visits:
        date_str = visit.visited_date.isoformat()
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'type': 'actual',
            'waypoint': visit.waypoint,
            'visit_note': visit,
            'time': visit.visited_date,
            'rating': visit.rating
        })

    # Рассчитываем предыдущий и следующий месяц
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'month_days': month_days,
        'events_by_date': events_by_date,
        'today': today,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    }

    return render(request, 'routes/visit_calendar.html', context)


@login_required
def calendar_events_json(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    if not start or not end:
        return JsonResponse({'error': 'Missing dates'}, status=400)

    start_date = datetime.fromisoformat(start.replace('Z', '+00:00')).date()
    end_date = datetime.fromisoformat(end.replace('Z', '+00:00')).date()

    # Запланированные посещения
    planned_visits = FavoriteWaypoint.objects.filter(
        user=request.user,
        planned_visit_date__isnull=False,
        planned_visit_date__gte=start_date,
        planned_visit_date__lte=end_date
    ).select_related('waypoint')

    # Совершенные посещения
    actual_visits = VisitNote.objects.filter(
        user=request.user,
        visited_date__gte=start_date,
        visited_date__lte=end_date
    ).select_related('waypoint')

    events = []

    for visit in planned_visits:
        events.append({
            'title': f"📅 {visit.waypoint.name}",
            'start': visit.planned_visit_date.isoformat(),
            'color': '#3498db',
            'textColor': 'white',
            'extendedProps': {
                'type': 'planned',
                'waypoint_id': visit.waypoint.id,
                'description': visit.waypoint.short_description
            }
        })

    for visit in actual_visits:
        color = '#27ae60' if visit.rating >= 4 else '#f39c12' if visit.rating >= 3 else '#e74c3c'
        events.append({
            'title': f"✅ {visit.waypoint.name} ({visit.rating}/5)",
            'start': visit.visited_date.isoformat(),
            'color': color,
            'textColor': 'white',
            'extendedProps': {
                'type': 'actual',
                'waypoint_id': visit.waypoint.id,
                'rating': visit.rating,
                'notes': visit.notes
            }
        })

    return JsonResponse(events, safe=False)


@login_required
def user_statistics(request):
    user = request.user

    # Основная статистика
    total_favorites = FavoriteWaypoint.objects.filter(user=user).count()
    total_visited = VisitNote.objects.filter(user=user).values('waypoint').distinct().count()
    total_personal_routes = PersonalRoute.objects.filter(user=user).count()

    # Статистика по типам точек
    favorite_types = FavoriteWaypoint.objects.filter(user=user).values(
        'waypoint__waypoint_type'
    ).annotate(count=Count('waypoint__waypoint_type')).order_by('-count')

    visited_types = VisitNote.objects.filter(user=user).values(
        'waypoint__waypoint_type'
    ).annotate(count=Count('waypoint__waypoint_type')).order_by('-count')

    # Самые популярные точки
    top_favorited = FavoriteWaypoint.objects.values(
        'waypoint__id', 'waypoint__name', 'waypoint__waypoint_type'
    ).annotate(count=Count('waypoint')).order_by('-count')[:10]

    # Лучше всего оцененные точки
    top_rated = VisitNote.objects.values(
        'waypoint__id', 'waypoint__name', 'waypoint__waypoint_type'
    ).annotate(avg_rating=Avg('rating')).filter(
        avg_rating__isnull=False
    ).order_by('-avg_rating')[:10]

    # Активность по месяцам
    from django.db.models.functions import TruncMonth
    monthly_activity = VisitNote.objects.filter(user=user).annotate(
        month=TruncMonth('visited_date')
    ).values('month').annotate(count=Count('id')).order_by('month')

    # Предстоящие посещения
    upcoming_visits = FavoriteWaypoint.objects.filter(
        user=user,
        planned_visit_date__isnull=False,
        planned_visit_date__gte=timezone.now().date()
    ).order_by('planned_visit_date')[:5]

    # Достижения
    achievements = []

    if total_visited >= 10:
        achievements.append({'name': 'Исследователь', 'description': 'Посетил 10 точек', 'icon': '🏆'})
    if total_favorites >= 20:
        achievements.append({'name': 'Коллекционер', 'description': 'Добавил 20 точек в избранное', 'icon': '⭐'})
    if total_personal_routes >= 5:
        achievements.append({'name': 'Планировщик', 'description': 'Создал 5 персональных маршрутов', 'icon': '🗺️'})

    # Самые продуктивные месяцы
    if monthly_activity:
        best_month = max(monthly_activity, key=lambda x: x['count'])
        achievements.append({
            'name': 'Активный путешественник',
            'description': f'Посетил {best_month["count"]} точек за один месяц',
            'icon': '🚀'
        })

    context = {
        'total_favorites': total_favorites,
        'total_visited': total_visited,
        'total_personal_routes': total_personal_routes,
        'favorite_types': favorite_types,
        'visited_types': visited_types,
        'top_favorited': top_favorited,
        'top_rated': top_rated,
        'monthly_activity': monthly_activity,
        'upcoming_visits': upcoming_visits,
        'achievements': achievements,
    }

    return render(request, 'routes/user_statistics.html', context)


@login_required
def statistics_json(request):
    user = request.user

    # Данные для графиков
    favorite_types_data = list(FavoriteWaypoint.objects.filter(user=user).values(
        'waypoint__waypoint_type'
    ).annotate(count=Count('waypoint__waypoint_type')).order_by('-count'))

    monthly_data = list(VisitNote.objects.filter(user=user).annotate(
        month=TruncMonth('visited_date')
    ).values('month').annotate(count=Count('id')).order_by('month'))

    rating_distribution = list(VisitNote.objects.filter(user=user).values(
        'rating'
    ).annotate(count=Count('id')).order_by('rating'))

    return JsonResponse({
        'favorite_types': favorite_types_data,
        'monthly_activity': monthly_data,
        'rating_distribution': rating_distribution
    })

