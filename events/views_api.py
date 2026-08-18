from django.http import JsonResponse, HttpResponseNotAllowed


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
