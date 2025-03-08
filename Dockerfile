FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
COPY .env .
RUN pip install --no-cache-dir -r requirements.txt

ENV DATABASE_URL=postgresql://postgres:postgres*ab@database-1.c67wkkcy8gel.us-east-1.rds.amazonaws.com:5432/postgres
ENV QUEUE_SERVICE=sqs
ENV SQS_URL=https://sqs.us-east-1.amazonaws.com/051826725299/supply_service_queue

# Configurar AWS CLI y credenciales
RUN pip install awscli

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]