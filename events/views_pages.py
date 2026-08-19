from django.shortcuts import render


def home(request):
    return render(request, "events/home.html")


def new_event(request):
    return render(request, "events/new_event.html")


def event_page(request, public_id):
    return render(request, "events/event_page.html", {"public_id": public_id})


def event_done(request, public_id):
    return render(request, "events/event_done.html", {"public_id": public_id})


def my_events_list(request):
    return render(request, "events/my_events.html")


def event_edit(request, public_id):
    return render(request, "events/event_edit.html", {"public_id": public_id})
