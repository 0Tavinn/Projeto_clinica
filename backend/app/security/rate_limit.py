"""
Rate limiting simples, em memória, para endpoints sensíveis (ex.: login).

LIMITAÇÃO CONHECIDA (documentada de propósito): este limiter guarda estado
no processo Python. Funciona corretamente com uma única instância/worker da
API. Em produção, com múltiplas réplicas, substitua por um backend
compartilhado (Redis, ex.: via slowapi + redis, ou um API Gateway com rate
limiting). Isolado em um módulo próprio exatamente para tornar essa troca
simples sem tocar nos routers.
"""
import time
from collections import defaultdict, deque

from fastapi import Depends, Request

from app.common.exceptions import AppError


class RateLimitExceededError(AppError):
    default_message = "Muitas tentativas. Tente novamente em instantes."


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window_start = now - self.window_seconds
        hits = self._hits[key]

        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= self.max_requests:
            raise RateLimitExceededError()

        hits.append(now)


# 5 tentativas por minuto por IP — alinhado ao LOGIN_RATE_LIMIT default de
# config.py. Para produção com múltiplos workers, trocar por store
# compartilhado (ver docstring do módulo).
login_rate_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)


def enforce_login_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    login_rate_limiter.check(f"login:{client_ip}")
