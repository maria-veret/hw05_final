from datetime import datetime
from django.http import HttpRequest, HttpResponse


def year(request: HttpRequest) -> HttpResponse:
    """Добавляет переменную с текущим годом."""
    dt = datetime.now().year
    return {
        'year': dt
    }
