FROM python:3.11-slim

WORKDIR /app

COPY services/identity/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/identity/ /app/identity
COPY shared/ /app/shared/

ENV PYTHONPATH=/app/identity:/app

EXPOSE 8000

CMD ["uvicorn", "identity.main:app", "--host", "0.0.0.0", "--port", "8000"]