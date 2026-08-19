from django.shortcuts import render


def home(request):
    return render(request, "events/home.html")


def edit(request):
    return render(request, "events/edit.html")


def event_page(request, public_id):
    return render(request, "events/event_page.html", {"public_id": public_id})


def post(request):#public_idテストのため一時的に削除
    return render(request, "events/post.html")#, {"public_id": public_id}テストのため一時的に削除
