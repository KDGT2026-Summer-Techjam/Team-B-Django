from django.urls import path

from . import views_api, views_pages

urlpatterns = [
    path("", views_pages.home, name="home"),
    path("edit", views_pages.edit, name="edit"),
    path("e/<str:public_id>/", views_pages.event_page, name="event_page"),
    path("post", views_pages.post, name="post"), #e/<str:public_id>あとで追加
    path("api/events", views_api.create_event, name="api_create_event"),
]
