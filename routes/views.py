from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Route, Waypoint


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