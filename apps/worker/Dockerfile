FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/apps/api

WORKDIR /workspace/apps/worker

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/api /workspace/apps/api
COPY apps/worker /workspace/apps/worker

CMD ["python", "main.py"]
