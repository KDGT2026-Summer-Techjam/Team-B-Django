from django.urls import path

from . import views_api, views_pages

urlpatterns = [
    path("", views_pages.home, name="home"),
    path("new", views_pages.new_event, name="new_event"),
    path("e/<str:public_id>/", views_pages.event_page, name="event_page"),
    path("done", views_pages.event_done, name="event_done"),#一時的にe/<str:public_id>/を削除
    path("e/<str:public_id>/edit", views_pages.event_edit, name="event_edit"),
    path("myevents", views_pages.my_events_list, name="my_events_list"),
    path("api/events", views_api.create_event, name="api_create_event"),
    path(
        "api/events/<str:public_id>",
        views_api.get_event,
        name="api_get_event",
    ),
    path(
        "api/events/<str:public_id>/join",
        views_api.join_event,
        name="api_join_event",
    ),
]
