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
```
