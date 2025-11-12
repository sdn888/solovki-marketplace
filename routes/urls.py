from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'routes'

urlpatterns = [
    path('', views.route_list, name='route_list'),
    path('<int:pk>/', views.route_detail, name='route_detail'),
    path('<int:pk>/geojson/', views.route_geojson, name='route_geojson'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('manager/dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('favorites/map/', views.favorite_waypoints_map, name='favorite_waypoints_map'),
    path('favorites/list/', views.favorite_waypoints_list, name='favorite_waypoints_list'),
    path('favorites/toggle/<int:waypoint_id>/', views.toggle_favorite_waypoint, name='toggle_favorite_waypoint'),
    # Персональные маршруты
    path('personal-routes/', views.PersonalRouteListView.as_view(), name='personal_routes_list'),
    path('personal-routes/create/', views.PersonalRouteCreateView.as_view(), name='personal_route_create'),
    path('personal-routes/<int:pk>/', views.PersonalRouteDetailView.as_view(), name='personal_route_detail'),
    path('personal-routes/<int:pk>/edit/', views.PersonalRouteUpdateView.as_view(), name='personal_route_edit'),
    path('personal-routes/<int:pk>/delete/', views.PersonalRouteDeleteView.as_view(), name='personal_route_delete'),
    path('personal-routes/<int:route_id>/add-point/<int:waypoint_id>/', views.add_point_to_personal_route, name='add_point_to_personal_route'),
    path('personal-routes/<int:route_id>/remove-point/<int:point_id>/', views.remove_point_from_personal_route, name='remove_point_from_personal_route'),
    path('personal-routes/<int:route_id>/update-order/', views.update_personal_route_points_order, name='update_personal_route_points_order'),
    # Заметки о посещениях
    path('visit-notes/create/', views.VisitNoteCreateView.as_view(), name='visit_note_create'),
    path('visit-notes/<int:pk>/edit/', views.VisitNoteUpdateView.as_view(), name='visit_note_edit'),
    # Обновление заметок для избранных точек
    path('favorites/update-notes/<int:waypoint_id>/', views.update_favorite_notes, name='update_favorite_notes'),
    # Экспорт
    path('personal-routes/<int:pk>/export/', views.export_personal_route_options, name='personal_route_export_options'),
    path('personal-routes/<int:pk>/export/<str:format_type>/', views.export_personal_route, name='export_personal_route'),

    # Совместные маршруты
    path('personal-routes/<int:pk>/share/', views.create_route_sharing, name='create_route_sharing'),
    path('shared-route/<str:token>/', views.view_shared_route, name='view_shared_route'),
    path('personal-routes/<int:pk>/add-collaborator/', views.add_collaborator, name='add_collaborator'),
    path('personal-routes/<int:pk>/add-comment/', views.add_route_comment, name='add_route_comment'),

    # Календарь
    path('calendar/', views.visit_calendar, name='visit_calendar'),
    path('calendar/<int:year>/<int:month>/', views.visit_calendar, name='visit_calendar_month'),
    path('calendar/events/', views.calendar_events_json, name='calendar_events_json'),

    # Статистика
    path('statistics/', views.user_statistics, name='user_statistics'),
    path('statistics/json/', views.statistics_json, name='statistics_json'),
]
