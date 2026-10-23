import secrets

VISITOR_ID_COOKIE_NAME = "visitor_id"
VISITOR_ID_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1年


def generate_visitor_id() -> str:
    return secrets.token_urlsafe(16)


class VisitorIdMiddleware:
    """未発行の場合はvisitor_idをCookieに発行し、request.visitor_idとして各viewに渡す"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        visitor_id = request.COOKIES.get(VISITOR_ID_COOKIE_NAME)
        should_issue = visitor_id is None
        if should_issue:
            visitor_id = generate_visitor_id()

        request.visitor_id = visitor_id
        response = self.get_response(request)

        # 未発行のとき、またはHTTPS（本番）のときは Cookie をセットする。
        # visitor_id はこのアプリの「ログイン」に当たるため、盗まれると他人のイベントを編集される。
        # そのため HTTPS では Secure を付ける（HTTPでは送らない）。
        # すでに Secure なしで発行済みの Cookie も、HTTPS でアクセスされたときに同じ値のまま
        # Secure 付きで再設定し、安全な属性に更新する（visitor_id の値は変わらない）。
        # ローカル開発（http://localhost）では is_secure() が False になり、これまでどおり動く。
        if should_issue or request.is_secure():
            response.set_cookie(
                VISITOR_ID_COOKIE_NAME,
                visitor_id,
                max_age=VISITOR_ID_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
                secure=request.is_secure(),
            )

        return response
