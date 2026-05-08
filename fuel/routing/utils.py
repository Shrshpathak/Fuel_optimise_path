# 

import math


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the straight-line distance between two latitude/longitude points.
    Returned distance is in miles.
    """

    earth_radius_miles = 3958.8

    lat_diff = math.radians(lat2 - lat1)
    lon_diff = math.radians(lon2 - lon1)

    a = (
        math.sin(lat_diff / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(lon_diff / 2) ** 2
    )

    return 2 * earth_radius_miles * math.asin(math.sqrt(a))


def build_route_mileposts(route_points, sample_every=6):
    """
    OpenRouteService returns thousands of coordinate points for long routes.
    Comparing every fuel station against every single route point becomes slow.

    To improve performance, the route is sampled every few miles while still
    keeping enough accuracy for nearby fuel station detection.

    Each sampled point stores:
    - latitude
    - longitude
    - cumulative distance from route start
    """

    if not route_points:
        return []

    sampled_points = [
        (
            route_points[0][0],
            route_points[0][1],
            0.0,
        )
    ]

    cumulative_distance = 0.0
    distance_since_last_sample = 0.0

    for index in range(1, len(route_points)):

        prev_lat, prev_lon = route_points[index - 1]
        curr_lat, curr_lon = route_points[index]

        segment_distance = haversine(
            prev_lat,
            prev_lon,
            curr_lat,
            curr_lon,
        )

        cumulative_distance += segment_distance
        distance_since_last_sample += segment_distance

        if distance_since_last_sample >= sample_every:
            sampled_points.append(
                (
                    curr_lat,
                    curr_lon,
                    round(cumulative_distance, 2),
                )
            )

            distance_since_last_sample = 0.0

    last_lat, last_lon = route_points[-1]

    if (
        last_lat != sampled_points[-1][0]
        or last_lon != sampled_points[-1][1]
    ):
        sampled_points.append(
            (
                last_lat,
                last_lon,
                round(cumulative_distance, 2),
            )
        )

    return sampled_points