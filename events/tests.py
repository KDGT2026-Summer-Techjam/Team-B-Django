import json
from datetime import date

from django.test import TestCase

from .models import Event, Participant


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


class EventPageTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
        )

    def test_event_page_context_marks_matching_visitor_as_participant(self):
        self.client.cookies["visitor_id"] = "visitor-a"
        Participant.objects.create(
            event=self.event,
            name="山田",
            visitor_id="visitor-a",
        )

        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["public_id"], self.event.public_id)
        self.assertEqual(response.context["event"], self.event)
        self.assertIs(response.context["is_participant"], True)
        self.assertNotIn("participants", response.context)

    def test_event_page_marks_visitor_without_participant_as_false(self):
        self.client.cookies["visitor_id"] = "visitor-a"

        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.context["is_participant"], False)

    def test_event_page_marks_different_participant_visitor_as_false(self):
        self.client.cookies["visitor_id"] = "visitor-a"
        Participant.objects.create(
            event=self.event,
            name="佐藤",
            visitor_id="visitor-b",
        )

        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.context["is_participant"], False)

    def test_event_page_returns_404_for_unknown_public_id(self):
        response = self.client.get("/e/zzzzzz/")

        self.assertEqual(response.status_code, 404)


class EventDoneTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
        )

    def test_event_done_page_returns_public_id_in_context(self):
        response = self.client.get(f"/e/{self.event.public_id}/done")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["public_id"], self.event.public_id)


class JoinEventTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
        )

    def post(self, payload):
        return self.client.post(
            f"/api/events/{self.event.public_id}/join",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_join_event_creates_participant_and_returns_participant_list(self):
        response = self.post({"name": "山田"})

        self.assertEqual(response.status_code, 201)
        participant = Participant.objects.get()
        self.assertEqual(participant.name, "山田")
        self.assertTrue(participant.visitor_id)
        self.assertEqual(
            response.json(),
            {
                "id": participant.id,
                "name": "山田",
                "participants": [{"id": participant.id, "name": "山田"}],
            },
        )

    def test_join_event_twice_with_same_visitor_id_does_not_duplicate(self):
        first_response = self.post({"name": "山田"})
        second_response = self.post({"name": "山田"})

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(Participant.objects.count(), 1)
        self.assertEqual(first_response.json(), second_response.json())

    def test_join_event_with_different_visitor_id_creates_another_participant(self):
        self.client.cookies["visitor_id"] = "visitor-a"
        self.post({"name": "山田"})

        self.client.cookies["visitor_id"] = "visitor-b"
        response = self.post({"name": "佐藤"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Participant.objects.count(), 2)

    def test_join_unknown_event_returns_404(self):
        response = self.client.post(
            "/api/events/zzzzzz/join",
            data=json.dumps({"name": "山田"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "イベントが見つかりません"})

    def test_join_event_without_name_returns_400(self):
        response = self.post({})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Participant.objects.exists())

    def test_join_event_with_blank_name_returns_400(self):
        response = self.post({"name": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Participant.objects.exists())

    def test_join_event_with_get_returns_405(self):
        response = self.client.get(f"/api/events/{self.event.public_id}/join")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["Allow"], "POST")
