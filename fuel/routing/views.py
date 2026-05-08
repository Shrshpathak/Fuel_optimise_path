

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import FuelPlanner, RouteService


@csrf_exempt
def plan_fuel_route(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required"},
            status=405,
        )

    try:
        payload = json.loads(request.body)

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON body"},
            status=400,
        )

    start = (payload.get("start") or "").strip()
    end = (payload.get("end") or "").strip()

    if not start or not end:
        return JsonResponse(
            {"error": "'start' and 'end' are required"},
            status=400,
        )

    try:
        route_service = RouteService()
        fuel_planner = FuelPlanner()

        start_coords = route_service.geocode(start)
        end_coords = route_service.geocode(end)

        (
            route_points,
            distance_miles,
            encoded_polyline,
        ) = route_service.get_route(
            start_coords,
            end_coords,
        )

        fuel_stops, total_fuel_cost = fuel_planner.plan(
            route_points,
            distance_miles,
        )

        response = {
            "start": start,
            "end": end,
            "distance_miles": round(distance_miles, 2),
            "total_gallons_needed": round(
                distance_miles / 10,
                2,
            ),
            "fuel_stops": fuel_stops,
            "total_fuel_cost": total_fuel_cost,
            "route_polyline": encoded_polyline,
        }

        return JsonResponse(response)

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

    except Exception as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=500,
        )