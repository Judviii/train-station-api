from datetime import datetime

from django.db.models import F, Count
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
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
from train_station.pagination import OrderPagination, JourneyPagination
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
    TrainImageSerializer,
    StationDetailSerializer,
    StationImageSerializer,
)


class StationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return StationDetailSerializer

        if self.action == "upload_image":
            return StationImageSerializer

        return StationSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific station"""
        station = self.get_object()
        serializer = self.get_serializer(station, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.errors, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RouteViewSet(
    ModelViewSet
):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")

        queryset = self.queryset.prefetch_related("source", "destination")

        if source:
            source_ids = self._params_to_ints(source)
            queryset = queryset.filter(source_id__in=source_ids)

        if destination:
            destination_ids = self._params_to_ints(destination)
            queryset = queryset.filter(destination_id__in=destination_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.prefetch_related(
        "tickets__journey__route",
        "tickets__journey__train",
        "tickets__journey__crew",
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

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

    def get_queryset(self):
        name = self.request.query_params.get("name")
        train_type = self.request.query_params.get("train_type")

        queryset = self.queryset.select_related("train_type")

        if name:
            queryset = queryset.filter(name__icontains=name)

        if train_type:
            queryset = queryset.filter(train_type_id=int(train_type))

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer
        if self.action == "upload_image":
            return TrainImageSerializer

        return TrainSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific train"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.errors, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CrewViewSet(ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class JourneyViewSet(ModelViewSet):
    queryset = (
        Journey.objects.all()
        .annotate(
            tickets_available=(
                    F("train__cargo_num") * F("train__places_in_cargo")
                    - Count("tickets")
            )
        )
    )
    serializer_class = JourneySerializer
    pagination_class = JourneyPagination

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

        if self.action == "retrieve":
            return queryset.prefetch_related("crew", "tickets")

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer

        if self.action == "retrieve":
            return JourneyDetailSerializer

        return JourneySerializer
