from django.urls import path

from . import views_api, views_pages

urlpatterns = [
    path("", views_pages.home, name="home"),
    path("new", views_pages.new_event, name="new_event"),
    path("e/<str:public_id>/", views_pages.event_page, name="event_page"),
    path("e/<str:public_id>/done", views_pages.event_done, name="event_done"),
    path("api/events", views_api.create_event, name="api_create_event"),
]
