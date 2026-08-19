from django.test import TestCase

from .models import Event, Participant


class GetEventTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
        )

    def test_get_event_returns_event_and_participants_in_join_order(self):
        first = Participant.objects.create(event=self.event, name="佐藤")
        second = Participant.objects.create(event=self.event, name="鈴木")

        response = self.client.get(f"/api/events/{self.event.public_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "public_id": self.event.public_id,
                "title": "長岡花火大会",
                "event_date": "2026-08-22",
                "location": "新潟県長岡市",
                "organizer_name": "田中",
                "participants": [
                    {"id": first.id, "name": "佐藤"},
                    {"id": second.id, "name": "鈴木"},
                ],
            },
        )
        self.assertNotIn("user", response.json())

    def test_get_event_returns_empty_participants(self):
        response = self.client.get(f"/api/events/{self.event.public_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["participants"], [])

    def test_get_unknown_event_returns_404(self):
        response = self.client.get("/api/events/zzzzzz")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "イベントが見つかりません"})

    def test_post_event_detail_returns_405(self):
        response = self.client.post(f"/api/events/{self.event.public_id}")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["Allow"], "GET")
