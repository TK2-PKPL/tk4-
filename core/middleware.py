from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponseForbidden


class TrustedOriginMiddleware:
    """Reject unsafe cross-origin write requests before view logic runs."""

    unsafe_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in self.unsafe_methods:
            origin = request.META.get("HTTP_ORIGIN")
            if origin and not self._is_allowed_origin(request, origin):
                return HttpResponseForbidden("Origin tidak diizinkan.")
        return self.get_response(request)

    def _is_allowed_origin(self, request, origin: str) -> bool:
        parsed_origin = urlparse(origin)
        if not parsed_origin.scheme or not parsed_origin.netloc:
            return False
        if parsed_origin.netloc == request.get_host():
            return True
        normalized_origin = f"{parsed_origin.scheme}://{parsed_origin.netloc}"
        return normalized_origin in set(getattr(settings, "CSRF_TRUSTED_ORIGINS", []))
