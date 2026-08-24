from django.shortcuts import render
from django.core.exceptions import DisallowedHost


class PlatformHealthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info == "/":
            try:
                request.get_host()
            except DisallowedHost:
                return render(request, "flujometro/app.html")
        return self.get_response(request)
