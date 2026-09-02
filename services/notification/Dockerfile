FROM python:3.11-slim

WORKDIR /app

COPY services/notification/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/notification/ /app/notification

COPY shared/ /app/shared/

ENV PYTHONPATH=/app/notification:/app

EXPOSE 8001

CMD ["uvicorn", "notification.main:app", "--host", "0.0.0.0", "--port", "8001"]