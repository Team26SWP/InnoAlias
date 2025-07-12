### Continuous Integration

Our CI pipeline lives in [`ci.yml`](.github/workflows/ci.yml) and is triggered on every pull-request that touches **backend**, **frontend** or **nginx** sources.

| Stage | Key tools | What we use them for |
|-------|-----------|----------------------|
| **Python lint** | **Black** · **Flake8** | *Black* (`black --check`) verifies that all backend Python code is auto-formatted; *Flake8* enforces PEP-8 style and flags unused imports, complexity, etc. |
| **Python type-check** | **mypy** | Ensures the backend respects the declared type hints and helps catch interface errors early. |
| **JS/TS lint** | **ESLint** | Checks React/TypeScript code for common bugs and style issues using our shared ESLint config. |
| **Backend tests** | **pytest** | Runs the unit and integration test-suite located in `backend/tests`, aborting after the first failure to keep feedback fast. |
| **Frontend tests** | **vitest** | Executes component and utility tests written for the React frontend. |
| **Image build** | **Docker Buildx** · **docker/login-action** | Builds and pushes backend, frontend and nginx images to Docker Hub (`latest` and SHA tags) once all checks pass. |

All runs of this workflow can be inspected in **GitHub Actions → CI**:  
`https://github.com/Team26SWP/InnoAlias/actions/workflows/ci.yml`
