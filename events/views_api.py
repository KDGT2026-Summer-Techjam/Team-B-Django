import json
import secrets

from django.http import HttpResponseNotAllowed, JsonResponse
from django.utils.dateparse import parse_date

from .models import Event, Participant

# 編集トークンはURLのクエリパラメータで受け取る（docs/設計.md「visitor_idの仕組み」）
EDIT_TOKEN_PARAM = "edit_token"
EDITABLE_FIELDS = ("title", "event_date", "location", "organizer_name")


def _matches(value, expected):
    """秘密の値どうしを、長さの差から内容を推測されない形で比較する。"""
    if not value:
        return False
    return secrets.compare_digest(value.encode(), expected.encode())


def can_edit_event(request, event):
    """編集トークンの一致、または作成者のvisitor_idの一致で編集を許可する。"""
    if _matches(request.GET.get(EDIT_TOKEN_PARAM), event.edit_token):
        return True
    return bool(event.creator_visitor_id) and _matches(
        request.visitor_id, event.creator_visitor_id
    )


def create_event(request):
    """イベントを作成し、共有に必要な情報を返す。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    required_fields = ("title", "event_date", "location", "organizer_name")
    if not isinstance(data, dict) or any(field not in data for field in required_fields):
        return JsonResponse({"error": "必須項目を入力してください"}, status=400)

    if not isinstance(data["organizer_name"], str) or not data["organizer_name"].strip():
        return JsonResponse({"error": "投稿者名を入力してください"}, status=400)

    if not all(
        isinstance(data[field], str) and data[field].strip()
        for field in ("title", "location")
    ):
        return JsonResponse({"error": "必須項目を入力してください"}, status=400)

    text_fields = ("title", "location", "organizer_name")
    cleaned_data = {field: data[field].strip() for field in text_fields}
    if any(
        len(cleaned_data[field]) > Event._meta.get_field(field).max_length
        for field in text_fields
    ):
        return JsonResponse({"error": "入力が長すぎます"}, status=400)

    if not isinstance(data["event_date"], str):
        return JsonResponse({"error": "日付が不正です"}, status=400)

    try:
        event_date = parse_date(data["event_date"])
    except ValueError:
        return JsonResponse({"error": "日付が不正です"}, status=400)
    if event_date is None or event_date.isoformat() != data["event_date"]:
        return JsonResponse({"error": "日付が不正です"}, status=400)

    # 作成者のvisitor_idを残す。編集画面の認可と、参加/作成イベントの集計に使う
    event = Event.objects.create(
        title=cleaned_data["title"],
        event_date=event_date,
        location=cleaned_data["location"],
        organizer_name=cleaned_data["organizer_name"],
        creator_visitor_id=request.visitor_id,
    )

    return JsonResponse(
        {
            "public_id": event.public_id,
            "edit_token": event.edit_token,
            "url": request.build_absolute_uri(f"/e/{event.public_id}"),
        },
        status=201,
    )


def get_event(request, public_id):
    """公開IDに対応するイベント情報と参加者一覧を返す。"""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    participants = [
        {"id": participant.id, "name": participant.name}
        for participant in event.participants.order_by("created_at", "id")
    ]

    return JsonResponse(
        {
            "public_id": event.public_id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "organizer_name": event.organizer_name,
            "participants": participants,
        }
    )


def event_detail(request, public_id):
    """公開IDに対応するイベントの取得(GET)と編集(PATCH)を振り分ける。"""
    if request.method == "GET":
        return get_event(request, public_id)
    if request.method == "PATCH":
        return update_event(request, public_id)
    return HttpResponseNotAllowed(["GET", "PATCH"])


def update_event(request, public_id):
    """イベントの内容を編集する。編集権限があるリクエストだけを受け付ける。"""
    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    if not can_edit_event(request, event):
        return JsonResponse({"error": "編集する権限がありません"}, status=403)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    fields = [field for field in EDITABLE_FIELDS if field in data]
    if not fields:
        return JsonResponse({"error": "編集する項目がありません"}, status=400)

    cleaned_data = {}
    for field in ("title", "location"):
        if field not in fields:
            continue
        if not isinstance(data[field], str) or not data[field].strip():
            return JsonResponse({"error": "必須項目を入力してください"}, status=400)
        cleaned_data[field] = data[field].strip()

    if "organizer_name" in fields:
        organizer_name = data["organizer_name"]
        if not isinstance(organizer_name, str) or not organizer_name.strip():
            return JsonResponse({"error": "投稿者名を入力してください"}, status=400)
        cleaned_data["organizer_name"] = organizer_name.strip()

    if any(
        len(value) > Event._meta.get_field(field).max_length
        for field, value in cleaned_data.items()
    ):
        return JsonResponse({"error": "入力が長すぎます"}, status=400)

    if "event_date" in fields:
        if not isinstance(data["event_date"], str):
            return JsonResponse({"error": "日付が不正です"}, status=400)
        try:
            event_date = parse_date(data["event_date"])
        except ValueError:
            return JsonResponse({"error": "日付が不正です"}, status=400)
        if event_date is None or event_date.isoformat() != data["event_date"]:
            return JsonResponse({"error": "日付が不正です"}, status=400)
        cleaned_data["event_date"] = event_date

    for field, value in cleaned_data.items():
        setattr(event, field, value)
    event.save(update_fields=list(cleaned_data))

    participants = [
        {"id": participant.id, "name": participant.name}
        for participant in event.participants.order_by("created_at", "id")
    ]

    return JsonResponse(
        {
            "public_id": event.public_id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "organizer_name": event.organizer_name,
            "participants": participants,
        }
    )


def join_event(request, public_id):
    """イベントに参加登録する。visitor_idで参加済みかを判定し、二重登録を防ぐ。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    if not isinstance(data, dict) or "name" not in data:
        return JsonResponse({"error": "名前を入力してください"}, status=400)

    if not isinstance(data["name"], str) or not data["name"].strip():
        return JsonResponse({"error": "名前を入力してください"}, status=400)

    name = data["name"].strip()
    max_length = Participant._meta.get_field("name").max_length
    if len(name) > max_length:
        return JsonResponse({"error": "入力が長すぎます"}, status=400)

    participant = event.participants.filter(visitor_id=request.visitor_id).first()
    status = 200
    if participant is None:
        participant = Participant.objects.create(
            event=event, name=name, visitor_id=request.visitor_id
        )
        status = 201

    participants = [
        {"id": p.id, "name": p.name}
        for p in event.participants.order_by("created_at", "id")
    ]

    return JsonResponse(
        {
            "id": participant.id,
            "name": participant.name,
            "participants": participants,
        },
        status=status,
    )

def my_events(request):
    #自分が参加中・作成済みのイベント一覧を返す。
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    visitor_id = request.visitor_id

    if not visitor_id:
        return JsonResponse({"events": []})

    participant_event_ids = set(
        Participant.objects.filter(
            visitor_id=visitor_id
        ).values_list("event_id", flat=True)
    )

    creator_event_ids = set(
        Event.objects.filter(
            creator_visitor_id=visitor_id
        ).values_list("id", flat=True)
    )

    event_ids = participant_event_ids | creator_event_ids

    events = Event.objects.filter(
        id__in=event_ids
    ).order_by("event_date")

    return JsonResponse(
        {
            "events": [
                {
                    "public_id": event.public_id,
                    "title": event.title,
                    "event_date": event.event_date.isoformat(),
                    "location": event.location,
                    "organizer_name": event.organizer_name,
                    "is_participant": event.id in participant_event_ids,
                    "is_creator": event.id in creator_event_ids,
                }
                for event in events
            ]
        }
    )
