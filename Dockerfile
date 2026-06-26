FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple/ -r requirements.txt

COPY . .

# Generar código Python desde los .proto fuente
RUN python -m grpc_tools.protoc \
    -I src/protos \
    --python_out=src/protos \
    --grpc_python_out=src/protos \
    src/protos/worker_service.proto \
    src/protos/event_service.proto \
    src/protos/common.proto

ENV PYTHONPATH=/app/src

EXPOSE 50053

CMD ["python", "src/main.py"]
