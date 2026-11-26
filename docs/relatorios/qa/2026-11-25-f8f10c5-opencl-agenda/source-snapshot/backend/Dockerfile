FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# PoCL fornece dispositivo CPU sem depender de GPU ou senha clínica.
RUN apt-get update && apt-get install -y --no-install-recommends pocl-opencl-icd ocl-icd-libopencl1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# O pacote exige README e app presentes durante a instalação.
COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts
RUN python -m pip install .
RUN useradd --create-home appuser
USER appuser
ARG SOURCE_COMMIT=unknown
LABEL org.opencontainers.image.revision=$SOURCE_COMMIT
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
