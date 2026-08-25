from django.urls import path

from . import views_api, views_pages

urlpatterns = [
    path("", views_pages.home, name="home"),
    path("new", views_pages.new_event, name="new_event"),
    path("e/<str:public_id>/", views_pages.event_page, name="event_page"),
    path("e/<str:public_id>/done", views_pages.event_done, name="event_done"),
    path("e/<str:public_id>/edit", views_pages.event_edit, name="event_edit"),
    path("myevents", views_pages.my_events_list, name="my_events_list"),
    path("api/events", views_api.create_event, name="api_create_event"),
    path(
        "api/events/<str:public_id>",
        views_api.event_detail,
        name="api_get_event",
    ),
    path(
        "api/events/<str:public_id>/participants",
        views_api.join_event,
        name="api_join_event",
    ),
    path(
        "api/events/<str:public_id>/missions/<str:mission_id>/photo",
        views_api.upload_mission_photo,
        name="api_upload_mission_photo",
    ),
    path(
    "api/my-events",
    views_api.my_events,
    name="api_my_events",
    ),
    path(
    "api/events/<str:public_id>/participants/<int:id>",
    views_api.delete_participant,
    name="api_delete_participant",
    ),
]
