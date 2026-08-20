from django.shortcuts import get_object_or_404, render

from .models import Event


def home(request):
    return render(request, "events/home.html")


def new_event(request):
    return render(request, "events/new_event.html")


def event_page(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    is_participant = event.participants.filter(
        visitor_id=request.visitor_id
    ).exists()
    return render(
        request,
        "events/event_page.html",
        {
            "public_id": public_id,
            "event": event,
            "is_participant": is_participant,
        },
    )


def event_done(request):#一時的に, public_idを削除
    return render(request, "events/event_done.html")#一時的に, {"public_id": public_id}を削除


def my_events_list(request):
    return render(request, "events/my_events.html")


def event_edit(request, public_id):
    return render(request, "events/event_edit.html", {"public_id": public_id})


def error_page(request, exception):
    return render(request, "events/error.html", status=404)
