# Imagem exclusiva dos ensaios; não modifica a API principal.
ARG APP_IMAGE=python:3.12-slim
FROM ${APP_IMAGE}
USER root
RUN python -m pip install 'pytest==9.1.1' 'httpx==0.28.1'
COPY tests /app/tests
COPY database /app/database
COPY scripts/benchmark_conflicts.py /app/scripts/benchmark_conflicts.py
USER appuser
ENV ENVIRONMENT=test DATABASE_URL=sqlite:///:memory: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 LUMINA_REQUIRE_OPENCL=1
