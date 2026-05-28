# NextWave SMS Backend - Development Instructions

## Project Overview
This project is a FastAPI-based backend integrated with Firebase (Auth and Firestore). It handles student records, company scores, and Excel data processing.

## Codebase Architecture
- **API Entry**: [app/main.py](app/main.py)
- **Routes**: Located in `app/routes/`.
- **Business Logic**: Handled in `app/services/`.
- **Data Models**: Defined in `app/models/` using Pydantic.
- **Utilities**: includes [app/utils/excel_parser.py](app/utils/excel_parser.py) and [app/utils/seeder.py](app/utils/seeder.py).

## Development Guidelines
1. **Redundancy Policy**: Avoid creating standalone scripts like `seed_db.py`. Database initialization is handled automatically in the `lifespan` event within [app/main.py](app/main.py).
2. **Environment**: Use [pyproject.toml](pyproject.toml) or [requirements.txt](requirements.txt) for dependencies. Remove `uv.lock` if not using the `uv` tool.
3. **Deployment**: `Dockerfile`, `docker-compose.yml`, and `cloudbuild.yaml` are optional and should only be modified if changing deployment strategies.
4. **Testing**: Currently, the codebase is lean; keep all files within the `app/` directory as they are tightly coupled.
