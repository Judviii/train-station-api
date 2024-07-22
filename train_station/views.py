from datetime import datetime

from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination
from django.db.models import F, Count

from rest_framework.viewsets import ModelViewSet
from train_station.models import (
    Station,
    Route,
    Order,
    TrainType,
    Train,
    Crew,
    Journey,
)

from train_station.serializers import (
    StationSerializer,
    RouteSerializer,
    TrainSerializer,
    OrderSerializer,
    TrainTypeSerializer,
    CrewSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    TrainListSerializer,
    TrainDetailSerializer,
    OrderListSerializer,
)


class StationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(
    ModelViewSet
):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer

    # filtering by Source / destination, distance?


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.prefetch_related(
        "tickets__journey__route", "tickets__journey__train"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TrainTypeViewSet(ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer
        return TrainSerializer


class CrewViewSet(ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class JourneyViewSet(ModelViewSet):
    queryset = (
        Journey.objects.all()
        .select_related("train", "route")
        .annotate(
            tickets_available=(
                    F("train__cargo_num") * F("train__places_in_cargo")
                    - Count("tickets")
            )
        )
    )
    serializer_class = JourneySerializer

    def get_queryset(self):
        departure_time = self.request.query_params.get("departure_time")
        route = self.request.query_params.get("route")

        queryset = self.queryset

        if departure_time:
            departure_time = datetime.strptime(
                departure_time, "%Y-%m-%d"
            ).date()
            queryset = queryset.filter(
                departure_time__date=departure_time
            )
        if route:
            queryset = queryset.filter(route_id=int(route))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer

        if self.action == "retrieve":
            return JourneyDetailSerializer

        return JourneySerializer
# filtering by departure time, route,
