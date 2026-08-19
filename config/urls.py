from django.urls import include, path

handler404 = "events.views_pages.error_page"

urlpatterns = [
    path("", include("events.urls")),
]
