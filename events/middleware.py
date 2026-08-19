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

        if should_issue:
            response.set_cookie(
                VISITOR_ID_COOKIE_NAME,
                visitor_id,
                max_age=VISITOR_ID_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
            )

        return response
