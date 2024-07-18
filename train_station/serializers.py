from rest_framework import serializers

from train_station.models import (
    Station,
    Route,
    Ticket,
    Order,
    TrainType,
    Train,
    Crew,
    Journey,
)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )


class RouteDetailSerializer(RouteSerializer):
    source = StationSerializer(many=False, read_only=True)
    destination = StationSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "created_at", "user")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey", "order")


class TicketListSerializer(TicketSerializer):
    journey = serializers.CharField(
        source="journey.route.complete_path", read_only=True
    )
    order_created_at = serializers.DateTimeField(source="order.created_at")

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey", "order_created_at")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "cargo_num", "places_in_cargo", "train_type")


class TrainListSerializer(TrainSerializer):
    train_type = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )


class TrainDetailSerializer(TrainSerializer):
    train_type = TrainTypeSerializer(many=False, read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = (
            "id", "route", "train", "departure_time", "arrival_time", "crew"
        )


class JourneyListSerializer(JourneySerializer):
    route = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="complete_path"
    )
    train = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )


class JourneyDetailSerializer(JourneySerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    travel_time = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "travel_time",
            "crew",
        )

    def get_travel_time(self, obj):
        duration = obj.arrival_time - obj.departure_time
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if days > 1:
            return f"{days} days, {hours} hours, {minutes} minutes"
        if hours > 1:
            return f"{hours} hours, {minutes} minutes"
        return f"{minutes} minutes"


