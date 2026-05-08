from django.urls import path
from . import views

urlpatterns = [
    path("route/", views.plan_fuel_route, name="plan_fuel_route"),
]
