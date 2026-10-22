# Employee Operations Platform

A containerized employee operations API built with FastAPI, PostgreSQL, and Redis. The project includes a Jenkins CI/CD pipeline that tests changes, builds and publishes a versioned Docker image, deploys it with Docker Compose, verifies application health, and rolls back to the previously deployed image if verification fails.

## Highlights

- Employee create, read, and update endpoints backed by PostgreSQL.
- Redis caching for individual employee lookups, with database fallback if Redis is unavailable.
- Docker Compose services for the API, PostgreSQL 17, and Redis 7 Alpine.
- Health checks for all services; the API waits for healthy database and Redis services before starting.
- API container limits of 512 MB memory and 1 CPU, with `unless-stopped` restart behavior.
- Jenkins stages for checkout, environment checks, virtual environment and dependency setup, tests, Docker build and push, deployment, health verification, and rollback.

## Architecture

| Component | Details |
| --- | --- |
| API | FastAPI, served by Uvicorn; container port `8000` is published as host port `8001` |
| Database | PostgreSQL 17, persisted in the named Docker volume `db_data` |
| Cache | Redis 7 Alpine |
| Image | `scratch2devops/employee-operations-platform:<tag>` |

The API container receives `DATABASE_URL`, `APP_NAME`, `LOG_LEVEL`, and `REDIS_URL` through Docker Compose. The database URL uses `DB_PASSWORD`, which Compose reads from the local `.env` file. The API health check calls `/health` inside the container.

## API

Implemented endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns `{"status":"healthy"}` |
| `GET` | `/employees` | Lists employees |
| `GET` | `/employees/{employee_id}` | Gets one employee; caches successful lookups in Redis |
| `POST` | `/employees` | Creates an employee |
| `PUT` | `/employees/{employee_id}` | Updates an employee |

Employee create and update requests use `name`, `email`, `department`, `designation`, and `salary`. Duplicate email on create returns HTTP `409`; requests for an unknown employee return HTTP `404`.

## Run locally with Docker Compose

### Prerequisites

- Git
- Docker Desktop or Docker Engine with the Docker Compose plugin
- A free host port `8001`

Clone the repository and move into its directory:

```bash
git clone https://github.com/scratch2devops/employee-operations-platform.git
cd employee-operations-platform
```

Create a `.env.example` template if the repository does not already contain one, then copy it to `.env`:

```dotenv
DB_PASSWORD=replace-with-a-local-development-password
```

```bash
cp .env.example .env
```

Replace the example value in `.env` with a local password before starting the stack. Keep `.env` private and do not commit real credentials. Compose requires `DB_PASSWORD` to be set.

Pull the images and start the services:

```bash
docker compose pull
docker compose up -d
```

Check the API health endpoint:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{"status":"healthy"}
```

The database data is retained in the named `db_data` volume when containers are stopped or recreated. To stop the local services while preserving that data, run `docker compose down`.

## Example API requests

Create an employee:

```bash
curl -X POST http://localhost:8001/employees \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alex Morgan","email":"alex@example.com","department":"Engineering","designation":"Software Engineer","salary":95000}'
```

List employees or retrieve one by ID:

```bash
curl http://localhost:8001/employees
curl http://localhost:8001/employees/1
```

Update an employee:

```bash
curl -X PUT http://localhost:8001/employees/1 \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alex Morgan","email":"alex@example.com","department":"Engineering","designation":"Senior Software Engineer","salary":110000}'
```

## Dependencies

Runtime dependencies are listed in `requirements.txt`:

- FastAPI `0.115.12`
- Uvicorn
- SQLAlchemy
- Pydantic
- python-dotenv
- psycopg with its binary extra
- redis-py

## CI/CD with Jenkins

The `Jenkinsfile` defines this delivery flow:

1. Check out the repository and report Python and Git versions.
2. Create a Python virtual environment and install `requirements-dev.txt`.
3. Run the test suite with pytest.
4. Build an image tagged with the Jenkins build number and push `scratch2devops/employee-operations-platform:<BUILD_NUMBER>` to Docker Hub.
5. Deploy the numbered image through Docker Compose and verify the container health check and `/health` response.
6. If the new deployment fails verification, restore the previously running image and verify it. The rollback path has been tested.

Configure these Jenkins credentials before running the pipeline:

| Jenkins credential ID | Type | Used for |
| --- | --- | --- |
| `employee-db-password` | Secret text | Supplies `DB_PASSWORD` during deployment |
| `scratch2devops` | Username and password | Authenticates Docker Hub image push and pull |

Store credentials in Jenkins Credentials. Do not put secret values in this README, source control, or the pipeline definition. The Jenkins agent needs Python 3, Git, Docker with Compose, network access to Docker Hub, and access to the deployment Docker daemon and Compose project.

## Run tests locally

The Jenkins pipeline installs development dependencies from `requirements-dev.txt`. To run the same test suite locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -v tests/
```

## Repository layout

```text
.
├── src/                 # FastAPI application, data models, and database setup
├── tests/               # API tests
├── Dockerfile           # API container image
├── docker-compose.yml   # API, PostgreSQL, and Redis services
├── Jenkinsfile          # CI/CD pipeline and deployment rollback
├── requirements.txt     # Runtime dependencies
└── requirements-dev.txt # Test and development dependencies
```
