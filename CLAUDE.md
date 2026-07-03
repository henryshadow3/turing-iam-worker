# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this service does

`turing-iam-worker` is a gRPC worker microservice handling Identity and Access Management (IAM) for the Turing platform. It registers itself on port `50053` as a `GenericWorker` and receives routed events (e.g., `iam.user.create.in`) from a central gateway service at `gateway-protobus:50051`.

The worker processes 14 IAM events across users, tenants, roles, and memberships — reading/writing a PostgreSQL database.

## Running the service

```bash
# Local dev
PYTHONPATH=src python src/main.py

# Docker
docker build -t turing-iam-worker .
docker run --env-file .env -p 50053:50053 turing-iam-worker
```

There is no test suite. There is no lint configuration.

## Regenerating protobuf stubs

The `*_pb2.py` and `*_pb2_grpc.py` files are **gitignored** and generated at Docker build time. After editing any `.proto` file, regenerate them manually:

```bash
python -m grpc_tools.protoc \
    -I src/protos \
    --python_out=src/protos \
    --grpc_python_out=src/protos \
    src/protos/worker_service.proto \
    src/protos/event_service.proto \
    src/protos/common.proto

# Fix import paths in generated grpc files
sed -i 's/^import \(.*_pb2\) as/from protos import \1 as/' src/protos/worker_service_pb2_grpc.py
sed -i 's/^import \(.*_pb2\) as/from protos import \1 as/' src/protos/event_service_pb2_grpc.py
sed -i 's/^import \(.*_pb2\) as/from protos import \1 as/' src/protos/common_pb2_grpc.py
```

## Architecture

The service follows hexagonal/clean architecture with three layers:

**`domain/`** — Pure Python dataclasses (entities) and abstract repository interfaces. No infrastructure dependencies.

**`application/`** — Use cases. `events_manager.py` holds the `ACTIONS` dict mapping event names to action functions. `business.py` dispatches incoming events to the right action. Each action in `application/actions/` follows this pattern:
1. Receives deserialized `data`, `context`, and a `DependencyContainer`
2. Gets a session manager and repository from the container
3. Calls the repository method
4. Returns `Ok(result)` or `Err(message)` using the `result` library

**`infrastructure/`** — All I/O. `SQLSessionManager` wraps a SQLModel `Session` as a context manager with a global `_engine` singleton. `DependencyContainer` is a factory for session managers and concrete repository instances. The concrete PostgreSQL repositories live in `infrastructure/repositories/`.

## Request flow

```
Gateway --> HandleAction(event_name, payload_bytes, context_bytes)
    --> IAMWorkerService.HandleAction()
    --> EventService.DeserializeEvent()  [callback to gateway]
    --> ACTIONS[event_name](data, context, container)
        --> repository method --> PostgreSQL
    --> EventService.ProcessEvent()      [callback to gateway to serialize response]
    --> ActionResponse(success, data_bytes)
```

## Key conventions

- **Railway-oriented error handling**: all repository methods and action functions return `Ok(value)` or `Err(str)` from the `result` library. Never raise exceptions as flow control.
- **Soft deletes**: membership "delete" (`iam.membership.delete.in`) sets `is_active = False` — it does not physically remove rows.
- **Password hashing**: done in the repository layer (`bcrypt`), not in the domain entity.
- **Database schemas**: the `turing` schema owns `tenants`, `roles`, `user_memberships`; the `brillaint_therapy` schema (typo is in source) owns `users`.
- **Registering a new event**: add the action function in `application/actions/`, then register it in the `ACTIONS` dict in `application/events_manager.py`.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_HOST` | `db-postgres` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `brilliant_sql` | Database name |
| `POSTGRES_USER` | `turing_admin` | DB user |
| `POSTGRES_PASSWORD` | _(required)_ | DB password |
| `GATEWAY_ADDRESS` | `gateway-protobus:50051` | Gateway gRPC address |
| `GRPC_PORT` | `50053` | Port this worker listens on |
| `ENABLE_TLS` | `false` | Enable mTLS for gateway connection |
