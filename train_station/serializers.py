from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError

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


class StationDetailSerializer(StationSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude", "image")


class StationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


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

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "image",
        )


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew",
        )


class JourneyListSerializer(JourneySerializer):
    route = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="complete_path"
    )
    train = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    train_capacity = serializers.IntegerField(
        source="train.capacity", read_only=True
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "train_capacity",
            "tickets_available",
            "crew",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["seat"],
            attrs["journey"].train,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey",)


class TicketListSerializer(TicketSerializer):
    journey = JourneyListSerializer(many=False, read_only=True)


class TicketSeatSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("cargo", "seat")


class JourneyDetailSerializer(JourneySerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_places = TicketSeatSerializer(
        source="tickets",
        many=True,
        read_only=True,
    )
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
            "taken_places",
            "crew",
        )

    def get_travel_time(self, obj):
        duration = obj.arrival_time - obj.departure_time
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        if hours > 0:
            return f"{hours} hours, {minutes} minutes"
        return f"{minutes} minutes"


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    @transaction.atomic()
    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
