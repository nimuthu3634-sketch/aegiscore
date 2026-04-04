FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/apps/api

WORKDIR /workspace/apps/worker

COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY api /workspace/apps/api
COPY worker /workspace/apps/worker

RUN useradd --create-home --shell /bin/bash aegis \
    && chown -R aegis:aegis /workspace

USER aegis

CMD ["python", "main.py"]
