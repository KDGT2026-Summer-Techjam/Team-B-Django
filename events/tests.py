import base64
import json
from datetime import date

from django.test import TestCase

from .models import Event, Mission, Participant


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


    def test_create_event_saves_visitor_id_as_creator(self):
        self.client.cookies["visitor_id"] = "creator-a"

        self.post(self.payload)

        self.assertEqual(Event.objects.get().creator_visitor_id, "creator-a")

    def test_create_event_saves_newly_issued_visitor_id_as_creator(self):
        """Cookieが無い初回アクセスでも、ミドルウェアが発行したvisitor_idを作成者として残す。"""
        response = self.post(self.payload)

        issued_visitor_id = response.cookies["visitor_id"].value
        self.assertTrue(issued_visitor_id)
        self.assertEqual(Event.objects.get().creator_visitor_id, issued_visitor_id)

    def test_creator_can_update_own_event_without_edit_token(self):
        """作成者は編集トークンを渡さなくても、自分のvisitor_idだけで編集できる。"""
        self.client.cookies["visitor_id"] = "creator-a"
        public_id = self.post(self.payload).json()["public_id"]

        response = self.client.patch(
            f"/api/events/{public_id}",
            data=json.dumps({"title": "長岡花火大会（雨天順延）"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Event.objects.get().title, "長岡花火大会（雨天順延）")

    def test_creator_can_open_edit_page_without_edit_token(self):
        self.client.cookies["visitor_id"] = "creator-a"
        public_id = self.post(self.payload).json()["public_id"]

        response = self.client.get(f"/e/{public_id}/edit")

        self.assertEqual(response.status_code, 200)

    def test_other_visitor_cannot_update_created_event(self):
        self.client.cookies["visitor_id"] = "creator-a"
        public_id = self.post(self.payload).json()["public_id"]

        self.client.cookies["visitor_id"] = "visitor-b"
        response = self.client.patch(
            f"/api/events/{public_id}",
            data=json.dumps({"title": "乗っ取り"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Event.objects.get().title, "長岡花火大会")


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
                "missions": [],
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

    def test_event_page_renders_participant_flag_for_participant(self):
        """JSが参加前／参加後の初期状態を決めるフラグをテンプレートが出力する"""
        self.client.cookies["visitor_id"] = "visitor-a"
        Participant.objects.create(
            event=self.event,
            name="山田",
            visitor_id="visitor-a",
        )

        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertIn('data-is-participant="true"', response.content.decode())

    def test_event_page_renders_participant_flag_for_non_participant(self):
        self.client.cookies["visitor_id"] = "visitor-a"

        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertIn('data-is-participant="false"', response.content.decode())

    def test_event_page_renders_public_id_for_api_call(self):
        """JSはbodyのdata-public-idを読んでAPIを呼ぶ"""
        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertIn(
            f'data-public-id="{self.event.public_id}"', response.content.decode()
        )

    def test_event_page_renders_elements_used_by_script(self):
        """event_page.jsが操作するIDがテンプレートに揃っている"""
        response = self.client.get(f"/e/{self.event.public_id}/")

        content = response.content.decode()
        for element_id in (
            "event-title",
            "event-date",
            "event-days-left",
            "event-location",
            "event-author",
            "event-member-count",
            "event-member-list",
            "event-join-area",
            "event-joined-message",
            "event-name-input",
            "event-join-btn",
            "event-error",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', content)

    def test_event_page_loads_event_page_script(self):
        response = self.client.get(f"/e/{self.event.public_id}/")

        # ManifestStaticFilesStorageがファイル名にハッシュを挟むため正規表現で照合する
        self.assertRegex(
            response.content.decode(), r"js/event_page(\.[0-9a-f]+)?\.js"
        )

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
            f"/api/events/{self.event.public_id}/participants",
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

    def test_join_event_twice_with_same_visitor_id_and_different_name_renames_participant(self):
        first_response = self.post({"name": "山田"})
        second_response = self.post({"name": "佐藤"})

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(Participant.objects.count(), 1)

        participant = Participant.objects.get()
        self.assertEqual(participant.name, "佐藤")
        self.assertEqual(
            second_response.json(),
            {
                "id": participant.id,
                "name": "佐藤",
                "participants": [{"id": participant.id, "name": "佐藤"}],
            },
        )

    def test_join_event_with_different_visitor_id_creates_another_participant(self):
        self.client.cookies["visitor_id"] = "visitor-a"
        self.post({"name": "山田"})

        self.client.cookies["visitor_id"] = "visitor-b"
        response = self.post({"name": "佐藤"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Participant.objects.count(), 2)

    def test_join_unknown_event_returns_404(self):
        response = self.client.post(
            "/api/events/zzzzzz/participants",
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
        response = self.client.get(f"/api/events/{self.event.public_id}/participants")

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


class CsrfTokenTests(TestCase):
    """docs/設計.md「CSRFの扱い」: POST/PATCH APIを呼ぶ画面はcsrftokenを発行する"""

    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
            creator_visitor_id="creator",
        )

    def test_new_event_page_issues_csrf_token(self):
        response = self.client.get("/new")

        self.assertIn("csrfmiddlewaretoken", response.content.decode())

    def test_event_page_issues_csrf_token(self):
        response = self.client.get(f"/e/{self.event.public_id}/")

        self.assertIn("csrfmiddlewaretoken", response.content.decode())

    def test_event_edit_page_issues_csrf_token(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.client.get(f"/e/{self.event.public_id}/edit")

        self.assertIn("csrfmiddlewaretoken", response.content.decode())


def make_photo(prefix="data:image/png;base64,", size=8):
    """テスト用のdata URL形式の写真データを作る。"""
    return prefix + base64.b64encode(b"a" * size).decode()


class CreateEventMissionTests(TestCase):
    def post(self, event_date):
        return self.client.post(
            "/api/events",
            data=json.dumps(
                {
                    "title": "長岡花火大会",
                    "event_date": event_date,
                    "location": "新潟県長岡市",
                    "organizer_name": "田中",
                }
            ),
            content_type="application/json",
        )

    def test_create_event_generates_three_missions(self):
        response = self.post("2026-08-22")

        self.assertEqual(response.status_code, 201)
        event = Event.objects.get()
        missions = list(event.missions.all())
        self.assertEqual([mission.order for mission in missions], [1, 2, 3])
        self.assertEqual(
            [mission.prompt_text for mission in missions],
            [
                "全員で写真を撮る",
                "みんなで食べたものを撮る",
                "夏ならではの1枚を撮る",
            ],
        )

    def test_generated_missions_start_uncleared(self):
        self.post("2026-08-22")

        event = Event.objects.get()
        for mission in event.missions.all():
            self.assertIsNone(mission.photo)
            self.assertIsNone(mission.completed_at)

    def test_third_mission_uses_season_of_event_date(self):
        cases = {
            "2026-04-05": "春ならではの1枚を撮る",
            "2026-08-22": "夏ならではの1枚を撮る",
            "2026-10-01": "秋ならではの1枚を撮る",
            "2026-12-24": "冬ならではの1枚を撮る",
            "2027-01-10": "冬ならではの1枚を撮る",
        }
        for event_date, expected in cases.items():
            with self.subTest(event_date=event_date):
                self.post(event_date)
                event = Event.objects.latest("id")
                self.assertEqual(event.missions.get(order=3).prompt_text, expected)


class GetEventMissionTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
        )

    def test_get_event_returns_missions_in_order(self):
        second = Mission.objects.create(
            event=self.event, order=2, prompt_text="みんなで食べたものを撮る"
        )
        first = Mission.objects.create(
            event=self.event, order=1, prompt_text="全員で写真を撮る"
        )

        response = self.client.get(f"/api/events/{self.event.public_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["missions"],
            [
                {
                    "id": first.id,
                    "order": 1,
                    "prompt_text": "全員で写真を撮る",
                    "photo": None,
                    "completed_at": None,
                },
                {
                    "id": second.id,
                    "order": 2,
                    "prompt_text": "みんなで食べたものを撮る",
                    "photo": None,
                    "completed_at": None,
                },
            ],
        )

    def test_get_event_returns_empty_missions_for_event_without_missions(self):
        response = self.client.get(f"/api/events/{self.event.public_id}")

        self.assertEqual(response.json()["missions"], [])

    def test_get_event_returns_photo_and_completed_at(self):
        photo = make_photo()
        self.client.cookies["visitor_id"] = "creator"
        self.event.creator_visitor_id = "creator"
        self.event.save(update_fields=["creator_visitor_id"])
        mission = Mission.objects.create(
            event=self.event, order=1, prompt_text="全員で写真を撮る"
        )
        self.client.post(
            f"/api/events/{self.event.public_id}/missions/{mission.id}/photo",
            data=json.dumps({"photo": photo}),
            content_type="application/json",
        )

        response = self.client.get(f"/api/events/{self.event.public_id}")

        returned = response.json()["missions"][0]
        self.assertEqual(returned["photo"], photo)
        self.assertIsNotNone(returned["completed_at"])


class UploadMissionPhotoTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="長岡花火大会",
            event_date="2026-08-22",
            location="新潟県長岡市",
            organizer_name="田中",
            creator_visitor_id="creator",
        )
        self.mission = Mission.objects.create(
            event=self.event, order=1, prompt_text="全員で写真を撮る"
        )

    def post(self, photo, mission_id=None, public_id=None):
        mission_id = self.mission.id if mission_id is None else mission_id
        public_id = self.event.public_id if public_id is None else public_id
        return self.client.post(
            f"/api/events/{public_id}/missions/{mission_id}/photo",
            data=json.dumps({"photo": photo}),
            content_type="application/json",
        )

    def join(self, visitor_id, name="山田"):
        self.client.cookies["visitor_id"] = visitor_id
        return self.client.post(
            f"/api/events/{self.event.public_id}/participants",
            data=json.dumps({"name": name}),
            content_type="application/json",
        )

    def test_participant_can_upload_photo(self):
        self.join("participant")
        photo = make_photo()

        response = self.post(photo)

        self.assertEqual(response.status_code, 200)
        self.mission.refresh_from_db()
        self.assertEqual(self.mission.photo, photo)
        self.assertIsNotNone(self.mission.completed_at)
        self.assertEqual(
            response.json(),
            {
                "id": self.mission.id,
                "order": 1,
                "prompt_text": "全員で写真を撮る",
                "photo": photo,
                "completed_at": response.json()["completed_at"],
            },
        )

    def test_creator_who_is_not_participant_can_upload_photo(self):
        self.client.cookies["visitor_id"] = "creator"
        self.assertFalse(self.event.participants.exists())

        response = self.post(make_photo())

        self.assertEqual(response.status_code, 200)
        self.mission.refresh_from_db()
        self.assertIsNotNone(self.mission.photo)

    def test_photo_is_overwritten(self):
        self.join("participant")
        self.post(make_photo(size=8))
        second_photo = make_photo(prefix="data:image/jpeg;base64,", size=16)

        response = self.post(second_photo)

        self.assertEqual(response.status_code, 200)
        self.mission.refresh_from_db()
        self.assertEqual(self.mission.photo, second_photo)

    def test_stranger_cannot_upload_photo(self):
        self.client.cookies["visitor_id"] = "stranger"

        response = self.post(make_photo())

        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())
        self.mission.refresh_from_db()
        self.assertIsNone(self.mission.photo)

    def test_visitor_without_cookie_cannot_upload_photo(self):
        response = self.post(make_photo())

        self.assertEqual(response.status_code, 403)
        self.mission.refresh_from_db()
        self.assertIsNone(self.mission.photo)

    def test_blank_visitor_id_does_not_match_participant_without_visitor_id(self):
        """participants.visitor_idはnull許容のため、空のvisitor_idは無条件で拒否する。"""
        from .views_api import can_upload_mission_photo

        Participant.objects.create(event=self.event, name="佐藤", visitor_id=None)

        class StubRequest:
            visitor_id = ""

        self.assertFalse(can_upload_mission_photo(StubRequest(), self.event))

    def test_upload_to_unknown_event_returns_404(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.post(make_photo(), public_id="zzzzzz")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "イベントが見つかりません"})

    def test_upload_to_unknown_mission_returns_404(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.post(make_photo(), mission_id=self.mission.id + 999)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "ミッションが見つかりません"})

    def test_upload_to_mission_of_another_event_returns_404(self):
        other_event = Event.objects.create(
            title="ぶどう狩り",
            event_date="2026-10-01",
            location="新潟県南魚沼市",
            organizer_name="鈴木",
        )
        other_mission = Mission.objects.create(
            event=other_event, order=1, prompt_text="全員で写真を撮る"
        )
        self.client.cookies["visitor_id"] = "creator"

        response = self.post(make_photo(), mission_id=other_mission.id)

        self.assertEqual(response.status_code, 404)
        other_mission.refresh_from_db()
        self.assertIsNone(other_mission.photo)

    def test_non_numeric_mission_id_returns_json_404(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.client.post(
            f"/api/events/{self.event.public_id}/missions/abc/photo",
            data=json.dumps({"photo": make_photo()}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "ミッションが見つかりません"})

    def test_accepts_base64_variations(self):
        """改行・パディング省略・大文字の接頭辞はいずれも復号できるため受け付ける。"""
        self.client.cookies["visitor_id"] = "creator"
        cases = {
            "改行入り": "data:image/png;base64,"
            + base64.encodebytes(b"a" * 100).decode(),
            "パディング省略": "data:image/png;base64,YWE",
            "大文字の接頭辞": "DATA:IMAGE/PNG;BASE64,YWFh",
        }
        for label, photo in cases.items():
            with self.subTest(label=label):
                response = self.post(photo)

                self.assertEqual(response.status_code, 200)
                self.mission.refresh_from_db()
                self.assertEqual(self.mission.photo, photo)

    def test_non_image_data_url_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.post(make_photo(prefix="data:text/html;base64,"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.mission.refresh_from_db()
        self.assertIsNone(self.mission.photo)

    def test_broken_base64_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.post("data:image/png;base64,これはBase64ではない")

        self.assertEqual(response.status_code, 400)
        self.mission.refresh_from_db()
        self.assertIsNone(self.mission.photo)

    def test_empty_photo_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.post("")

        self.assertEqual(response.status_code, 400)
        self.mission.refresh_from_db()
        self.assertIsNone(self.mission.photo)

    def test_accepts_jpeg_and_webp(self):
        self.client.cookies["visitor_id"] = "creator"
        for prefix in ("data:image/jpeg;base64,", "data:image/webp;base64,"):
            with self.subTest(prefix=prefix):
                response = self.post(make_photo(prefix=prefix))

                self.assertEqual(response.status_code, 200)

    def test_photo_over_size_limit_returns_400(self):
        self.client.cookies["visitor_id"] = "creator"
        prefix = "data:image/png;base64,"
        photo = prefix + "A" * (5 * 1024 * 1024)

        response = self.post(photo)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "写真のサイズが大きすぎます"})
        self.mission.refresh_from_db()
        self.assertIsNone(self.mission.photo)

    def test_three_megabyte_photo_is_accepted(self):
        """DATA_UPLOAD_MAX_MEMORY_SIZEを上げていないとDjangoが400を返す。"""
        self.client.cookies["visitor_id"] = "creator"
        photo = make_photo(size=2 * 1024 * 1024)
        self.assertGreater(len(photo), 2.5 * 1024 * 1024)

        response = self.post(photo)

        self.assertEqual(response.status_code, 200)
        self.mission.refresh_from_db()
        self.assertEqual(self.mission.photo, photo)

    def test_get_returns_405(self):
        self.client.cookies["visitor_id"] = "creator"

        response = self.client.get(
            f"/api/events/{self.event.public_id}/missions/{self.mission.id}/photo"
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["Allow"], "POST")
