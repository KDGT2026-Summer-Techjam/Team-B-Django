from django.http import JsonResponse, HttpResponseNotAllowed

from .models import Event


def create_event(request):
    """POST /api/events のダミー実装。固定値を返すのみで、DBには書き込まない。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    return JsonResponse(
        {
            "public_id": "a7k2m9",
            "edit_token": "dummy-edit-token",
            "url": "http://127.0.0.1:8000/e/a7k2m9",
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
