from django.utils.html import strip_tags


def get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def sanitize_text(value: str) -> str:
    if value is None:
        return ""
    return strip_tags(str(value)).replace("<", "").replace(">", "").strip()
