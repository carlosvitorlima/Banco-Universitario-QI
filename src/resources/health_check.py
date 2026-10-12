import os
from fastapi import Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from constants import SERVICE_NAME
from database import get_context
from utils.logger import get_logger

logger = get_logger(__name__)


class HealthCheckResource:
    """As duas rotas que respondem sem token: quem é este serviço, e se ele está vivo/pronto."""

    def on_get_home(self) -> JSONResponse:
        home = {"service": SERVICE_NAME, "id": str(os.getpid())}
        return JSONResponse(content=home, status_code=status.HTTP_200_OK)

    def on_get_health_check(self) -> Response:
        try:
            context = get_context()
            session = context.get_or_create_session()
            session.execute(text("SELECT 1"))
            
            return Response(status_code=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Readiness probe falhou: {e}")
            return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)