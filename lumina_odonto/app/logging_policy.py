"""Política de logs Uvicorn sem valores clínicos de URLs ou exceções."""

import logging
from starlette.routing import compile_path

_METHODS = {"GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS", "HEAD"}
_SERVER_EVENTS = {
    "Started server process [%d]": "process_started",
    "Waiting for application startup.": "startup_waiting",
    "Application startup complete.": "startup_complete",
    "Shutting down": "shutdown_started",
    "Waiting for application shutdown.": "shutdown_waiting",
    "Application shutdown complete.": "shutdown_complete",
    "Finished server process [%d]": "process_finished",
    "Invalid HTTP request received.": "invalid_http_request",
}


class ClinicalAccessFilter(logging.Filter):
    """Reconstrói o registro antes do formatter, descartando msg/args originais.

    Usa a rota estática da aplicação, sem querystring nem valores do caminho.
    Rotas inexistentes ficam sem o caminho arbitrário enviado pelo cliente.
    Os cinco argumentos preservam a compatibilidade com AccessFormatter.
    """

    def __init__(self, routes):
        super().__init__()
        self.routes = routes

    def filter(self, record):
        method, path, status, version = "OTHER", "[unmatched]", 500, "unknown"
        if isinstance(record.args, tuple) and len(record.args) == 5:
            _, supplied_method, supplied_path, supplied_version, supplied_status = record.args
            if supplied_version in ("1.0", "1.1"):
                version = supplied_version
            if supplied_method in _METHODS:
                method = supplied_method
            if isinstance(supplied_status, int) and 100 <= supplied_status <= 599:
                status = supplied_status
            if isinstance(supplied_path, str):
                supplied_path = supplied_path.split("?", 1)[0]
                for route_path, path_regex in self.routes:
                    if path_regex.fullmatch(supplied_path):
                        path = route_path
                        break
        record.msg = '%s - "%s %s HTTP/%s" %d'
        record.args = ("-", method, path, version, status)
        record.exc_info = record.exc_text = record.stack_info = None
        record.__dict__.pop("color_message", None)
        return True


class ClinicalServerFilter(logging.Filter):
    """Mantém eventos operacionais e impede reintroduzir entradas por traceback.

    Exceções podem carregar parâmetros SQL e texto clínico. O log registra
    somente o evento e o nível; a investigação detalhada exige ensaio seguro.
    """

    def filter(self, record):
        if record.exc_info or record.levelno >= logging.ERROR:
            event = "server_error"
        else:
            event = _SERVER_EVENTS.get(record.msg, "server_event") if isinstance(record.msg, str) else "server_event"
        record.msg = "server_event=%s"
        record.args = (event,)
        record.exc_info = record.exc_text = record.stack_info = None
        record.__dict__.pop("color_message", None)
        return True


def install_logging_policy(app):
    """Aplica a política também ao CMD original e ao uvicorn app.main:app.

    Uvicorn configura seus loggers antes de importar a aplicação. Os filtros
    atuam antes dos formatters e não dependem de flags externas do ensaio.
    """
    # FastAPI pode manter routers incluídos indiretamente em app.routes.
    # O contrato público fornece também seus caminhos já prefixados.
    routes = {route.path: route.path_regex for route in app.routes
              if hasattr(route, "path_regex")}
    for path in app.openapi()["paths"]:
        routes.setdefault(path, compile_path(path)[0])
    routes = tuple(routes.items())
    for name, policy in (
        ("uvicorn.access", ClinicalAccessFilter(routes)),
        ("uvicorn.error", ClinicalServerFilter()),
        ("uvicorn", ClinicalServerFilter()),
    ):
        logger = logging.getLogger(name)
        logger.filters[:] = [item for item in logger.filters
                             if not isinstance(item, type(policy))]
        logger.addFilter(policy)
