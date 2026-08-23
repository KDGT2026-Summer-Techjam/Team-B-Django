import base64
import binascii
import json
import secrets

from django.http import HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Event, Mission, Participant

# 編集画面の表示はURLのクエリパラメータで編集トークンを受け取る
# （docs/設計.md「visitor_idの仕組み」）
EDIT_TOKEN_PARAM = "edit_token"
# 更新APIはURLに載せず、ヘッダかリクエストボディで受け取る
EDIT_TOKEN_HEADER = "X-Edit-Token"
EDITABLE_FIELDS = ("title", "event_date", "location", "organizer_name")
# ミッションの文言。後から変えたくなったときに1箇所で済むよう定数で持つ
MISSION_PROMPTS = (
    "全員で写真を撮る",
    "みんなで食べたものを撮る",
    "{season}ならではの1枚を撮る",
)
# 季節の区分はdocs/設計.mdの季節エフェクトの表に合わせる
SEASON_BY_MONTH = {
    1: "冬",
    2: "冬",
    3: "春",
    4: "春",
    5: "春",
    6: "夏",
    7: "夏",
    8: "夏",
    9: "秋",
    10: "秋",
    11: "秋",
    12: "冬",
}
# 受け付ける写真の形式。緩くするとdata:text/htmlなどを保存されてしまう
PHOTO_DATA_URL_PREFIXES = (
    "data:image/jpeg;base64,",
    "data:image/png;base64,",
    "data:image/webp;base64,",
)
# Base64文字列の長さで5MB（元画像で約3.75MB相当）
PHOTO_MAX_LENGTH = 5 * 1024 * 1024


def _matches(value, expected):
    """秘密の値どうしを、長さの差から内容を推測されない形で比較する。"""
    if not value:
        return False
    return secrets.compare_digest(value.encode(), expected.encode())


def can_edit_event(request, event, edit_token):
    """編集トークンの一致、または作成者のvisitor_idの一致で編集を許可する。

    トークンをどこから読むかは呼び出し側で決める。編集画面の表示はURLのクエリ、
    更新APIはヘッダかリクエストボディで受け取る。
    """
    if _matches(edit_token, event.edit_token):
        return True
    return bool(event.creator_visitor_id) and _matches(
        request.visitor_id, event.creator_visitor_id
    )


def _update_edit_token(request, data):
    """更新APIの編集トークンを読む。ヘッダを優先し、無ければボディを見る。

    URLのクエリは見ない。履歴やRefererからトークンが漏れるため。
    """
    header_token = request.headers.get(EDIT_TOKEN_HEADER)
    if header_token:
        return header_token

    # ボディはJSONなので文字列以外の値も届く
    body_token = data.get(EDIT_TOKEN_PARAM)
    return body_token if isinstance(body_token, str) else None


def create_missions(event):
    """イベント作成時にミッションを自動生成する。他に登録する手段が無いため。"""
    season = SEASON_BY_MONTH[event.event_date.month]
    Mission.objects.bulk_create(
        [
            Mission(event=event, order=order, prompt_text=prompt.format(season=season))
            for order, prompt in enumerate(MISSION_PROMPTS, start=1)
        ]
    )


def _mission_json(mission):
    """ミッション1件分のJSONを組み立てる。photoがnullなら未クリア。"""
    completed_at = mission.completed_at
    return {
        "id": mission.id,
        "order": mission.order,
        "prompt_text": mission.prompt_text,
        "photo": mission.photo,
        "completed_at": (
            timezone.localtime(completed_at).isoformat() if completed_at else None
        ),
    }


def _missions_json(event):
    """ミッション一覧をorderの昇順で返す。未登録のイベントでは空配列になる。"""
    return [_mission_json(mission) for mission in event.missions.all()]


def _is_supported_photo(photo):
    """data URLの形式と、続きがBase64として復号できることを確かめる。"""
    # data URLのMIME部分は大文字小文字を区別しない
    lowered = photo.lower()
    for prefix in PHOTO_DATA_URL_PREFIXES:
        if lowered.startswith(prefix):
            encoded = photo[len(prefix) :]
            break
    else:
        return False

    # 一部のエンコーダが挿入する改行や空白は、復号できるので取り除いて判定する
    encoded = "".join(encoded.split())
    if not encoded:
        return False

    # パディングが省略されていても復号できるように補う
    encoded += "=" * (-len(encoded) % 4)

    try:
        base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return False
    return True


def can_upload_mission_photo(request, event):
    """そのイベントの参加者、または作成者だけがミッション写真を登録できる。

    編集トークンは使わない（参加者は持っていないため）。作成者がparticipantsに
    入っていないことがあるので、参加者と作成者の2条件で判定する。
    """
    visitor_id = request.visitor_id
    # participants.visitor_idはnull許容のため、空のまま絞り込むと誰でも通ってしまう
    if not visitor_id:
        return False

    if event.participants.filter(visitor_id=visitor_id).exists():
        return True

    return bool(event.creator_visitor_id) and _matches(
        visitor_id, event.creator_visitor_id
    )


def create_event(request):
    """イベントを作成し、共有に必要な情報を返す。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    required_fields = ("title", "event_date", "location", "organizer_name")
    if not isinstance(data, dict) or any(field not in data for field in required_fields):
        return JsonResponse({"error": "必須項目を入力してください"}, status=400)

    if not isinstance(data["organizer_name"], str) or not data["organizer_name"].strip():
        return JsonResponse({"error": "投稿者名を入力してください"}, status=400)

    if not all(
        isinstance(data[field], str) and data[field].strip()
        for field in ("title", "location")
    ):
        return JsonResponse({"error": "必須項目を入力してください"}, status=400)

    text_fields = ("title", "location", "organizer_name")
    cleaned_data = {field: data[field].strip() for field in text_fields}
    if any(
        len(cleaned_data[field]) > Event._meta.get_field(field).max_length
        for field in text_fields
    ):
        return JsonResponse({"error": "入力が長すぎます"}, status=400)

    if not isinstance(data["event_date"], str):
        return JsonResponse({"error": "日付が不正です"}, status=400)

    try:
        event_date = parse_date(data["event_date"])
    except ValueError:
        return JsonResponse({"error": "日付が不正です"}, status=400)
    if event_date is None or event_date.isoformat() != data["event_date"]:
        return JsonResponse({"error": "日付が不正です"}, status=400)

    # 作成者のvisitor_idを残す。編集画面の認可と、参加/作成イベントの集計に使う
    event = Event.objects.create(
        title=cleaned_data["title"],
        event_date=event_date,
        location=cleaned_data["location"],
        organizer_name=cleaned_data["organizer_name"],
        creator_visitor_id=request.visitor_id,
    )
    create_missions(event)

    return JsonResponse(
        {
            "public_id": event.public_id,
            "edit_token": event.edit_token,
            "url": request.build_absolute_uri(f"/e/{event.public_id}"),
        },
        status=201,
    )


def get_event(request, public_id):
    """公開IDに対応するイベント情報と参加者一覧を返す。"""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    participants = [
        {"id": participant.id, "name": participant.name}
        for participant in event.participants.order_by("created_at", "id")
    ]

    return JsonResponse(
        {
            "public_id": event.public_id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "organizer_name": event.organizer_name,
            "participants": participants,
            "missions": _missions_json(event),
        }
    )


def event_detail(request, public_id):
    """公開IDに対応するイベントの取得(GET)と編集(PATCH)を振り分ける。"""
    if request.method == "GET":
        return get_event(request, public_id)
    if request.method == "PATCH":
        return update_event(request, public_id)
    return HttpResponseNotAllowed(["GET", "PATCH"])


def update_event(request, public_id):
    """イベントの内容を編集する。編集権限があるリクエストだけを受け付ける。"""
    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    # トークンをボディからも読むため、認可判定より先に読み取る
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    if not can_edit_event(request, event, _update_edit_token(request, data)):
        return JsonResponse({"error": "編集する権限がありません"}, status=403)

    fields = [field for field in EDITABLE_FIELDS if field in data]
    if not fields:
        return JsonResponse({"error": "編集する項目がありません"}, status=400)

    cleaned_data = {}
    for field in ("title", "location"):
        if field not in fields:
            continue
        if not isinstance(data[field], str) or not data[field].strip():
            return JsonResponse({"error": "必須項目を入力してください"}, status=400)
        cleaned_data[field] = data[field].strip()

    if "organizer_name" in fields:
        organizer_name = data["organizer_name"]
        if not isinstance(organizer_name, str) or not organizer_name.strip():
            return JsonResponse({"error": "投稿者名を入力してください"}, status=400)
        cleaned_data["organizer_name"] = organizer_name.strip()

    if any(
        len(value) > Event._meta.get_field(field).max_length
        for field, value in cleaned_data.items()
    ):
        return JsonResponse({"error": "入力が長すぎます"}, status=400)

    if "event_date" in fields:
        if not isinstance(data["event_date"], str):
            return JsonResponse({"error": "日付が不正です"}, status=400)
        try:
            event_date = parse_date(data["event_date"])
        except ValueError:
            return JsonResponse({"error": "日付が不正です"}, status=400)
        if event_date is None or event_date.isoformat() != data["event_date"]:
            return JsonResponse({"error": "日付が不正です"}, status=400)
        cleaned_data["event_date"] = event_date

    for field, value in cleaned_data.items():
        setattr(event, field, value)
    event.save(update_fields=list(cleaned_data))

    participants = [
        {"id": participant.id, "name": participant.name}
        for participant in event.participants.order_by("created_at", "id")
    ]

    return JsonResponse(
        {
            "public_id": event.public_id,
            "title": event.title,
            "event_date": event.event_date.isoformat(),
            "location": event.location,
            "organizer_name": event.organizer_name,
            "participants": participants,
        }
    )


def join_event(request, public_id):
    """イベントに参加登録する。visitor_idで参加済みかを判定し、二重登録を防ぐ。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    if not isinstance(data, dict) or "name" not in data:
        return JsonResponse({"error": "名前を入力してください"}, status=400)

    if not isinstance(data["name"], str) or not data["name"].strip():
        return JsonResponse({"error": "名前を入力してください"}, status=400)

    name = data["name"].strip()
    max_length = Participant._meta.get_field("name").max_length
    if len(name) > max_length:
        return JsonResponse({"error": "入力が長すぎます"}, status=400)

    participant = event.participants.filter(visitor_id=request.visitor_id).first()
    status = 200
    if participant is None:
        participant = Participant.objects.create(
            event=event, name=name, visitor_id=request.visitor_id
        )
        status = 201
    else:
        participant.name = name
        participant.save()

    participants = [
        {"id": p.id, "name": p.name}
        for p in event.participants.order_by("created_at", "id")
    ]

    return JsonResponse(
        {
            "id": participant.id,
            "name": participant.name,
            "participants": participants,
        },
        status=status,
    )


def upload_mission_photo(request, public_id, mission_id):
    """ミッションの写真を登録する。参加者または作成者だけが実行できる。"""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        event = Event.objects.get(public_id=public_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "イベントが見つかりません"}, status=404)

    if not can_upload_mission_photo(request, event):
        return JsonResponse({"error": "写真を登録する権限がありません"}, status=403)

    # 他のイベントのミッションIDや、数値でないIDを渡された場合も404にする
    try:
        mission = event.missions.get(id=mission_id)
    except (Mission.DoesNotExist, ValueError):
        return JsonResponse({"error": "ミッションが見つかりません"}, status=404)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "リクエストが不正です"}, status=400)

    photo = data.get("photo")
    if not isinstance(photo, str) or not photo:
        return JsonResponse({"error": "写真データが空です"}, status=400)

    if len(photo) > PHOTO_MAX_LENGTH:
        return JsonResponse({"error": "写真のサイズが大きすぎます"}, status=400)

    if not _is_supported_photo(photo):
        return JsonResponse({"error": "写真の形式が不正です"}, status=400)

    # 1ミッション1枚のため、既に写真があるときは上書きする
    mission.photo = photo
    mission.completed_at = timezone.now()
    mission.save(update_fields=["photo", "completed_at"])

    return JsonResponse(_mission_json(mission))


def my_events(request):
    #自分が参加中・作成済みのイベント一覧を返す。
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    visitor_id = request.visitor_id

    if not visitor_id:
        return JsonResponse({"events": []})

    participant_event_ids = set(
        Participant.objects.filter(
            visitor_id=visitor_id
        ).values_list("event_id", flat=True)
    )

    creator_event_ids = set(
        Event.objects.filter(
            creator_visitor_id=visitor_id
        ).values_list("id", flat=True)
    )

    event_ids = participant_event_ids | creator_event_ids

    events = Event.objects.filter(
        id__in=event_ids
    ).order_by("event_date")

    return JsonResponse(
        {
            "events": [
                {
                    "public_id": event.public_id,
                    "title": event.title,
                    "event_date": event.event_date.isoformat(),
                    "location": event.location,
                    "organizer_name": event.organizer_name,
                    "is_participant": event.id in participant_event_ids,
                    "is_creator": event.id in creator_event_ids,
                }
                for event in events
            ]
        }
    )
