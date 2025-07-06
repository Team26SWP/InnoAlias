## Usage

## Architecture
### Static view

### Dynamic view

### Deployment view

## Development
### Kanban board
Entry criteria for each kanban board column:
#### Backlog (in discussion)
- The entry is agreed to be added (requested by the customer/determined to be necessary for development)
- The entry is still being thought through / discussed upon
#### Ready (to be picked up)
- The entry is in its final state
- All prerequisites for its development are satisfied
#### In progress
- A developer (or few) is assigned to this entry
- The entry is actively being worked on
#### Review
- The assignee(s) finished working on the entry
- A pull request was created
- Review from other team members was requested
#### Done
- The entry was reviewed and confirmed to be done
- The entry satisfies the customer's requests, if any
- The pull request was merged

### Git workflow

### Secrets management

## Quality assurance
### Quality attribute scenarios
https://github.com/Team26SWP/InnoAlias/blob/ca1317b7fe61124c86f485a1d6afc69a71eaa774/docs/quality-assurance/quality-attribute-scenarios.md
### Automated tests
**Tools used:**
- **Vitest** – for frontend unit and integration tests (TypeScript/React).  
- **React Testing Library** (`@testing-library/react`, `@testing-library/user-event`) – for testing React components 
- **pytest + pytest-asyncio** – for backend unit and integration tests (FastAPI)
- **mongomock_motor**, **httpx.AsyncClient**, **TestClient** – mock database and HTTP clients for integration tests 
- **ESLint** – static analysis of frontend code

**Types of tests:**
1. **Frontend unit/integration tests**  
   Verify individual React components and their interactions (rendering, user input, validation)
2. **Backend unit tests**  
   Test service logic and helper functions (ID generators, game logic, validation)
3. **Backend integration tests**  
   End-to-end HTTP flows: registration, login, profile retrieval, game creation and retrieval, leaderboard export
4. **Static analysis**  
   - **Frontend:** ESLint  
   - **Backend:** Black, Flake8, Mypy  


**Test locations:**

| Test type                       | Path in repository                                       |
|---------------------------------|----------------------------------------------------------|
| Frontend unit/integration       | `frontend/tests/components/*.test.tsx`                   |
| Frontend test setup             | `frontend/tests/setup.ts`                                |
| Frontend config (Vitest)        | `frontend/vitest.config.ts`                              |
| Backend unit tests              | `backend/tests/test_code_gen_unit.py`                    |
|                                 | `backend/tests/test_game_service_unit.py`                |
|                                 | `backend/tests/test_auth_unit.py`                        |
| Backend integration tests       | `backend/tests/test_integration.py`                      |
| Backend test fixtures & setup   | `backend/tests/_test_setup.py`                           |
|                                 | `backend/tests/conftest.py`                              |
| Static analysis (lint)          | `.eslintrc.js` (run via `npm run lint` on the frontend)  |

**Running tests and linting:**
```bash
# Frontend
npm run test           # Vitest
npm run test -- --coverage
npm run lint           # ESLint

# Backend
pytest -q              # run all backend tests
flake8 backend         # lint Python code
black --check backend  # check Python formatting
mypy backend           # static type checking

### User acceptance tests
See [user tests](/docs/quality-assurance/user-acceptance-tests.md)

## Build and deployment
### Continuous Integration

### Continuous Deployment


