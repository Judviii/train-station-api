import tempfile
import os
import uuid
from datetime import datetime

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from train_station.models import (
    Station,
    Route,
    TrainType,
    Train,
    Crew,
    Journey
)
from train_station.serializers import (
    RouteListSerializer,
    TrainListSerializer,
    JourneyListSerializer, JourneySerializer
)

TRAIN_URL = reverse("train_station:train-list")
ROUTE_URL = reverse("train-station:route-list")
JOURNEY_URL = reverse("train-station:journey-list")


def station_image_upload_url(station_id):
    return reverse(
        "train-station:station-upload-image", args=[station_id]
    )


def station_detail_url(station_id):
    return reverse(
        "train-station:station-detail",
        kwargs={"pk": station_id}
    )


def train_image_upload_url(train_id):
    return reverse(
        "train-station:train-upload-image",
        kwargs={"pk": train_id}
    )


def train_detail_url(train_id):
    return reverse("train-station:train-detail", args=[train_id])


def sample_train(**params):
    train_type = TrainType.objects.create(name=f"Test {uuid.uuid4()}")
    defaults = {
        "name": f"Sample Train {uuid.uuid4()}",
        "cargo_num": 20,
        "places_in_cargo": 10,
        "train_type": train_type,
    }
    defaults.update(params)
    return Train.objects.create(**defaults)


def sample_station(**params):
    defaults = {
        "name": f"Sample Station {uuid.uuid4()}",
        "latitude": 1.0,
        "longitude": 2.0,
    }
    defaults.update(params)
    return Station.objects.create(**defaults)


def sample_route(**params):
    defaults = {
        "source": sample_station(),
        "destination": sample_station(),
        "distance": 1,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_crew(**params):
    defaults = {
        "first_name": "John",
        "last_name": "Smith",
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_journey(**params):
    departure_time = datetime.strptime(
        "2024-08-22 10:00:00", "%Y-%m-%d %H:%M:%S"
    )
    arrival_time = datetime.strptime("2024-08-23 15:00:00", "%Y-%m-%d %H:%M:%S")
    crew = [sample_crew()]
    defaults = {
        "route": sample_route(),
        "train": sample_train(),
        "departure_time": departure_time,
        "arrival_time": arrival_time,
    }
    defaults.update(params)
    journey = Journey.objects.create(**defaults)
    journey.crew.set(crew)
    return journey


class UnauthenticatedTrainStationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainStationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@case.test", password="test123password"
        )
        self.client.force_authenticate(self.user)

    def test_route_list(self):
        sample_route()

        res = self.client.get(ROUTE_URL)
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_routes_by_source(self):
        route_1 = sample_route()
        route_2 = sample_route()
        route_3 = sample_route()

        res = self.client.get(
            ROUTE_URL, {
                "source": f"{route_2.source.id}, {route_3.source.id}"
            }
        )

        serializer_1 = RouteListSerializer(route_1)
        serializer_2 = RouteListSerializer(route_2)
        serializer_3 = RouteListSerializer(route_3)

        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertIn(serializer_3.data, res.data)

        res = self.client.get(
            ROUTE_URL, {"source": f"{route_1.source.id}"}
        )

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_filter_routes_by_destination(self):
        route_1 = sample_route()
        route_2 = sample_route()
        route_3 = sample_route()

        res = self.client.get(
            ROUTE_URL, {
                "destination": f"{route_2.destination.id}, "
                               f"{route_3.destination.id}"
            }
        )

        serializer_1 = RouteListSerializer(route_1)
        serializer_2 = RouteListSerializer(route_2)
        serializer_3 = RouteListSerializer(route_3)

        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertIn(serializer_3.data, res.data)

        res = self.client.get(
            ROUTE_URL, {"destination": f"{route_1.destination.id}"}
        )

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_filter_train_by_name(self):
        train_1 = sample_train()
        train_2 = sample_train(name="TEST1")
        train_3 = sample_train(name="TEST2")

        serializer_1 = TrainListSerializer(train_1)
        serializer_2 = TrainListSerializer(train_2)
        serializer_3 = TrainListSerializer(train_3)

        res = self.client.get(
            TRAIN_URL,
            {"name": "TEST"}
        )

        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertIn(serializer_3.data, res.data)

        res = self.client.get(
            TRAIN_URL,
            {"name": "Sample"}
        )

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_filter_train_by_train_type(self):
        train_1 = sample_train()
        train_2 = sample_train()

        res = self.client.get(
            TRAIN_URL,
            {
                "train_type": f"{train_1.train_type.id}"
            }
        )

        serializer_1 = TrainListSerializer(train_1)
        serializer_2 = TrainListSerializer(train_2)

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

        res = self.client.get(
            TRAIN_URL,
            {"train_type": f"{train_2.train_type.id}"}
        )

        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)

    def test_filter_journey_by_departure_time(self):
        journey_1 = sample_journey(departure_time="2024-08-28T10:00:00Z")
        journey_2 = sample_journey(departure_time="2024-08-29T10:00:00Z")

        serializer_1 = JourneyListSerializer(journey_1)
        serializer_2 = JourneyListSerializer(journey_2)

        res = self.client.get(JOURNEY_URL,
                                   {"departure_time": "2024-08-28"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        response_data = res.json().get("results", [])

        serialized_data_1 = serializer_1.data
        serialized_data_2 = serializer_2.data

        self.assertTrue(
            any(
                item['id'] == serialized_data_1['id']
                for item in response_data
            )
        )
        self.assertFalse(
            any(
                item['id'] == serialized_data_2['id']
                for item in response_data
            )
        )

    def test_filter_journey_by_route(self):
        route_1 = sample_route()
        route_2 = sample_route()
        journey_1 = sample_journey(route=route_1)
        journey_2 = sample_journey(route=route_2)

        res = self.client.get(
            JOURNEY_URL,
            {"route": f"{journey_1.route.id}"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer1 = JourneyListSerializer(journey_1)
        serializer2 = JourneyListSerializer(journey_2)

        self.assertEqual(
            serializer1.data["id"], res.data["results"][-1]["id"]
        )
        self.assertNotEqual(
            serializer2.data["id"], res.data["results"][-1]["id"]
        )


class AdminTrainStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@case.test",
            password="test123password",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_journey(self):
        route = sample_route()
        train = sample_train()
        journey = sample_journey(route=route, train=train)

        serializer = JourneySerializer(journey)
        journey_data = serializer.data

        res = self.client.post(JOURNEY_URL, journey_data, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_journey_without_train(self):
        route = sample_route()
        crew = [sample_crew()]

        journey_data = {
            "route": route.id,
            "train": "Not a train",
            "departure_time": "2024-08-22T10:00:00Z",
            "arrival_time": "2024-08-23T15:00:00Z",
            "crew": [crew[0].id]
        }

        res = self.client.post(JOURNEY_URL, journey_data, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("train", res.data)

    def test_create_journey_without_route(self):
        train = sample_train()
        crew = [sample_crew()]

        journey_data = {
            "train": train.id,
            "departure_time": "2024-08-22T10:00:00Z",
            "arrival_time": "2024-08-23T15:00:00Z",
            "crew": [crew[0].id]
        }

        res = self.client.post(JOURNEY_URL, journey_data, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route", res.data)

    def test_create_journey_without_crew(self):
        route = sample_route()
        train = sample_train()

        journey_data = {
            "route": route.id,
            "train": train.id,
            "departure_time": "2024-08-22T10:00:00Z",
            "arrival_time": "2024-08-23T15:00:00Z"
        }

        res = self.client.post(JOURNEY_URL, journey_data, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("crew", res.data)


class StationImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@case.test",
            password="test123password",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)
        self.station = sample_station()

    def tearDown(self):
        self.station.image.delete()

    def test_upload_image_to_station(self):
        url = station_image_upload_url(self.station.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.station.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(os.path.exists(self.station.image.path))

    def test_upload_image_bad_request(self):
        url = station_image_upload_url(self.station.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@case.test",
            password="test123password",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)
        self.train = sample_train()

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_station(self):
        url = train_image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        url = train_image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
