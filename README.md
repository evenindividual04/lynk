# Lynk

Semi-automated LinkedIn outreach and networking system.

## Setup

```bash
make setup
```

This installs Python deps (uv), JS deps (pnpm), runs migrations, and installs pre-commit hooks.

## Development

```bash
make dev          # start both backend (:8000) and frontend (:5173)
make backend      # backend only
make frontend     # frontend only
```

## Testing

```bash
make test         # run all tests (backend + frontend)
```

## Database

```bash
make migrate      # run pending migrations
make migrate-create msg="description"  # create new migration
```

## Type generation

After changing backend API routes:

```bash
# Start backend first, then:
make gen-types    # regenerates frontend/openapi-types.ts
```

## Import

Drop your LinkedIn `Connections.csv` into `data/imports/` or use the `/imports` page in the UI.
