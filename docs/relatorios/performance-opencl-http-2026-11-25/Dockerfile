ARG BASE=python:3.12-slim
FROM ${BASE}
USER root
RUN python -m pip install httpx==0.28.1
COPY instrumented_app.py measure_http.py /measurement/
USER appuser
CMD ["python", "/measurement/measure_http.py"]
