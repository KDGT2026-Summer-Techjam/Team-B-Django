import json
from datetime import date

from django.test import TestCase

from .models import Event


class CreateEventTests(TestCase):
    def setUp(self):
        self.payload = {
            "title": "長岡花火大会",
            "event_date": "2026-08-22",
            "location": "新潟県長岡市",
            "organizer_name": "田中",
        }

    def post(self, payload):
        return self.client.post(
            "/api/events",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_create_event_saves_event_and_returns_creation_credentials(self):
        response = self.post(self.payload)

        self.assertEqual(response.status_code, 201)
        event = Event.objects.get()
        self.assertEqual(event.title, "長岡花火大会")
        self.assertEqual(event.event_date, date(2026, 8, 22))
        self.assertEqual(event.location, "新潟県長岡市")
        self.assertEqual(event.organizer_name, "田中")
        self.assertEqual(
            response.json(),
            {
                "public_id": event.public_id,
                "edit_token": event.edit_token,
                "url": f"http://testserver/e/{event.public_id}",
            },
        )

    def test_missing_required_field_returns_400(self):
        del self.payload["location"]

        response = self.post(self.payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Event.objects.exists())

    def test_invalid_date_returns_400(self):
        self.payload["event_date"] = "2026-02-30"

        response = self.post(self.payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Event.objects.exists())

    def test_non_string_date_returns_400(self):
        self.payload["event_date"] = 20260822

        response = self.post(self.payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Event.objects.exists())

    def test_empty_organizer_name_returns_400(self):
        self.payload["organizer_name"] = "   "

        response = self.post(self.payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Event.objects.exists())

    def test_text_field_over_max_length_returns_400_without_saving(self):
        for field in ("title", "location", "organizer_name"):
            with self.subTest(field=field):
                max_length = Event._meta.get_field(field).max_length
                payload = {**self.payload, field: "あ" * (max_length + 1)}

                response = self.post(payload)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"error": "入力が長すぎます"})
                self.assertFalse(Event.objects.exists())

    def test_text_field_at_max_length_returns_201(self):
        for field in ("title", "location", "organizer_name"):
            with self.subTest(field=field):
                max_length = Event._meta.get_field(field).max_length
                payload = {**self.payload, field: "あ" * max_length}

                response = self.post(payload)

                self.assertEqual(response.status_code, 201)
                Event.objects.all().delete()
