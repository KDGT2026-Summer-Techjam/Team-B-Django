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
        self.assertEqual(response.headers["Allow"], "GET, PATCH")


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


class UpdateEventTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
            creator_visitor_id="creator",
        )
        self.payload = {
            "title": "長岡花火大会（雨天順延）",
            "event_date": "2026-08-23",
            "location": "新潟県長岡市 信濃川河川敷",
            "organizer_name": "田中太郎",
        }

    def patch(self, payload, token=None):
        url = f"/api/events/{self.event.public_id}"
        if token is not None:
            url = f"{url}?edit_token={token}"
        return self.client.patch(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_creator_visitor_can_update_event(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.patch(self.payload)

        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "長岡花火大会（雨天順延）")
        self.assertEqual(self.event.event_date, date(2026, 8, 23))
        self.assertEqual(self.event.location, "新潟県長岡市 信濃川河川敷")
        self.assertEqual(self.event.organizer_name, "田中太郎")
        self.assertEqual(
            response.json(),
            {
                "public_id": self.event.public_id,
                "title": "長岡花火大会（雨天順延）",
                "event_date": "2026-08-23",
                "location": "新潟県長岡市 信濃川河川敷",
                "organizer_name": "田中太郎",
                "participants": [],
            },
        )

    def test_edit_token_allows_update_from_another_visitor(self):
        self.client.cookies["visitor_id"] = "someone-else"

        response = self.patch(self.payload, token=self.event.edit_token)

        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "長岡花火大会（雨天順延）")

    def test_update_response_does_not_include_edit_token(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.patch(self.payload)

        self.assertNotIn("edit_token", response.json())

    def test_update_applies_only_sent_fields(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.patch({"title": "長岡花火大会2026"})

        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "長岡花火大会2026")
        self.assertEqual(self.event.location, "新潟県長岡市")
        self.assertEqual(self.event.event_date, date(2026, 8, 22))

    def test_update_returns_participants(self):
        self.client.cookies["visitor_id"] = "creator"
        participant = Participant.objects.create(event=self.event, name="佐藤")

        response = self.patch({"title": "長岡花火大会2026"})

        self.assertEqual(
            response.json()["participants"],
            [{"id": participant.id, "name": "佐藤"}],
        )

    def test_update_without_permission_returns_403(self):
        self.client.cookies["visitor_id"] = "someone-else"

        response = self.patch(self.payload)

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "長岡花火大会")

    def test_update_with_wrong_token_returns_403(self):
        self.client.cookies["visitor_id"] = "someone-else"

        response = self.patch(self.payload, token="wrong-token")

        self.assertEqual(response.status_code, 403)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "長岡花火大会")

    def test_update_event_without_creator_visitor_id_requires_token(self):
        event = Event.objects.create(
            title="ぶどう狩り",
            event_date="2026-10-01",
            location="新潟県南魚沼市",
            organizer_name="鈴木",
        )

        response = self.client.patch(
            f"/api/events/{event.public_id}",
            data=json.dumps({"title": "ぶどう狩り2026"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.title, "ぶどう狩り")

    def test_update_unknown_event_returns_404(self):
        response = self.client.patch(
            "/api/events/zzzzzz",
            data=json.dumps(self.payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "イベントが見つかりません"})

    def test_update_with_invalid_date_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.patch({"event_date": "2026-02-30"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "日付が不正です"})
        self.event.refresh_from_db()
        self.assertEqual(self.event.event_date, date(2026, 8, 22))

    def test_update_with_blank_title_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.patch({"title": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "長岡花火大会")

    def test_update_with_blank_organizer_name_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.patch({"organizer_name": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "投稿者名を入力してください"})

    def test_update_with_too_long_title_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"
        max_length = Event._meta.get_field("title").max_length

        response = self.patch({"title": "あ" * (max_length + 1)})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "入力が長すぎます"})

    def test_update_without_editable_field_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"
        public_id = self.event.public_id

        response = self.patch({"public_id": "aaaaaa"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "編集する項目がありません"})
        self.event.refresh_from_db()
        self.assertEqual(self.event.public_id, public_id)

    def test_update_with_broken_json_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.client.patch(
            f"/api/events/{self.event.public_id}",
            data="{",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())


class EventEditPageTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
            creator_visitor_id="creator",
        )

    def test_creator_visitor_can_open_edit_page(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.client.get(f"/e/{self.event.public_id}/edit")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_edit.html")
        self.assertEqual(response.context["public_id"], self.event.public_id)

    def test_edit_page_does_not_expose_edit_token(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.client.get(f"/e/{self.event.public_id}/edit")

        self.assertNotIn("event", response.context)
        self.assertNotIn(self.event.edit_token, response.content.decode())

    def test_edit_token_allows_opening_edit_page(self):
        self.client.cookies["visitor_id"] = "someone-else"

        response = self.client.get(
            f"/e/{self.event.public_id}/edit?edit_token={self.event.edit_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_edit.html")

    def test_edit_page_without_permission_returns_error_page_with_403(self):
        self.client.cookies["visitor_id"] = "someone-else"

        response = self.client.get(f"/e/{self.event.public_id}/edit")

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "events/error.html")

    def test_edit_page_with_wrong_token_returns_403(self):
        self.client.cookies["visitor_id"] = "someone-else"

        response = self.client.get(
            f"/e/{self.event.public_id}/edit?edit_token=wrong-token"
        )

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "events/error.html")

    def test_edit_page_for_unknown_public_id_returns_404(self):
        response = self.client.get("/e/zzzzzz/edit")

        self.assertEqual(response.status_code, 404)
