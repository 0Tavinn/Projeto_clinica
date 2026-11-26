"""Regressões de privacidade para registros operacionais e exceções."""

import logging
import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://qa:qa@localhost/qa")
os.environ.setdefault("JWT_SECRET", "qa-only-not-for-production-0000000000")
from app.main import app


@pytest.mark.parametrize("name", ["uvicorn", "uvicorn.error"])
def test_exception_and_message_are_not_rendered(name, caplog):
    logger = logging.getLogger(name)
    sentinel = "PRIVATE_LOG_SENTINEL"
    with caplog.at_level(logging.INFO):
        try:
            raise RuntimeError(sentinel)
        except RuntimeError:
            logger.error("request_url=%s", sentinel, exc_info=True)
        logger.warning("unexpected=%s", sentinel, extra={"color_message": sentinel})
    assert sentinel not in caplog.text
    assert "server_error" in caplog.text
    assert all(record.exc_info is None and record.exc_text is None
               and record.stack_info is None for record in caplog.records)


@pytest.mark.parametrize("version", ["1.0", "1.1"])
@pytest.mark.parametrize("request_path,route", [
    ("/api/v1/clinical/search?q=PRIVATE_LOG_SENTINEL", "/api/v1/clinical/search"),
    ("/api/v1/patients/123/record?q=PRIVATE_LOG_SENTINEL", "/api/v1/patients/{patient_id}/record"),
    ("/unknown/PRIVATE_LOG_SENTINEL?q=PRIVATE_LOG_SENTINEL", "[unmatched]"),
])
def test_access_keeps_operational_fields_without_values(request_path, route, version, caplog):
    with caplog.at_level(logging.INFO):
        logging.getLogger("uvicorn.access").info(
            '%s - "%s %s HTTP/%s" %d',
            "PRIVATE_LOG_SENTINEL", "GET", request_path, version, 422,
        )
    assert "PRIVATE_LOG_SENTINEL" not in caplog.text
    assert route in caplog.text
    assert "GET" in caplog.text and "422" in caplog.text
    assert "HTTP/"+version in caplog.text
