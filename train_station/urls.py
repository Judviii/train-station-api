from rest_framework import routers
from django.urls import path, include

from train_station.views import (
    StationViewSet,
    RouteViewSet,
    OrderViewSet,
    TrainTypeViewSet,
    TrainViewSet,
    CrewViewSet,
    JourneyViewSet,
)

router = routers.DefaultRouter()
router.register("stations", StationViewSet)
router.register("routes", RouteViewSet)
router.register("orders", OrderViewSet)
router.register("train_types", TrainTypeViewSet)
router.register("trains", TrainViewSet)
router.register("crews", CrewViewSet)
router.register("journeys", JourneyViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "train_station"
