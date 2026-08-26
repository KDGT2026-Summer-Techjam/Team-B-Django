from django.shortcuts import get_object_or_404, render

from .models import Event
from .views_api import EDIT_TOKEN_PARAM, can_edit_event


def home(request):
    return render(request, "events/home.html")


def new_event(request):
    return render(request, "events/new_event.html")


def event_page(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    is_participant = event.participants.filter(
        visitor_id=request.visitor_id
    ).exists()
    is_creator = bool(event.creator_visitor_id) and (
        event.creator_visitor_id == request.visitor_id
    )
    return render(
        request,
        "events/event_page.html",
        {
            "public_id": public_id,
            "event": event,
            "is_participant": is_participant,
            "is_creator": is_creator,
        },
    )


def event_done(request, public_id):
    return render(request, "events/event_done.html", {"public_id": public_id})


def my_events_list(request):
    return render(request, "events/my_events.html")


def event_edit(request, public_id):
    """編集画面。編集権限が無ければエラー画面を403で返す。"""
    event = get_object_or_404(Event, public_id=public_id)
    # 画面の表示はリンクから開くため、トークンはURLのクエリで受け取る
    if not can_edit_event(request, event, request.GET.get(EDIT_TOKEN_PARAM)):
        return render(request, "events/error.html", status=403)
    return render(request, "events/event_edit.html", {"public_id": public_id})


def error_page(request, exception):
    return render(request, "events/error.html", status=404)
