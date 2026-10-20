from django.db import connection
from rest_framework.views import APIView

from .responses import success_response


class HealthView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database = "ok"
        except Exception:  # noqa: BLE001 - health must never raise
            database = "unavailable"
        return success_response({"status": "ok" if database == "ok" else "degraded", "database": database})
