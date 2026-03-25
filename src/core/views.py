import logging

from django.db import OperationalError, connection
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'core/home.html'


def healthcheck_view(request):
    try:
        connection.ensure_connection()
    except OperationalError as exc:
        logger.error("Healthcheck DB bağlantısı başarısız: %s", exc)
        return HttpResponseServerError("db_unavailable", content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")


def permission_denied_view(request, exception):
    return render(request, '403.html', status=403)


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


def server_error_view(request):
    return render(request, '500.html', status=500)
