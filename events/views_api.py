import json

from django.http import HttpResponseNotAllowed, JsonResponse
from django.utils.dateparse import parse_date

from .models import Event

from .models import Event


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

    event = Event.objects.create(
        title=cleaned_data["title"],
        event_date=event_date,
        location=cleaned_data["location"],
        organizer_name=cleaned_data["organizer_name"],
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
