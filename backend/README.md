# InnoAlias Backend

This folder contains a FastAPI backend for a game.


## Usage (locally)
1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Copy `.env.example` **from the repository root** to `.env`:
   ```bash
   cp .env.example .env # it must be under InnoAlias/.env
   ```
3. Modify .env:
   ```bash
   nano .env # specify all entries
   ```
   The backend uses MongoDB. Set `MONGO_URI` to point at your database instance
   (default is `mongodb://localhost:27017/`).
4. Run the server **from the repository root:**
   ```bash
    python -m uvicorn backend.app.main:app --reload
   ```

## Running Tests

Install test dependencies and run:

```bash
pytest -q
```

Additional API documentation can be found under `backend/docs/API.md`.


## Structure

```
backend/
    requirements.txt  # project dependencies
    Dockerfile        # dockerfile for building the backend container
    
    app/
        main.py       # FastAPI application
        db.py         # database connection
        config.py     # config for auth
        code_gen.py   # code generator for the game
        services/     # services for API
        routers/      # API and websocket routers
        models/       # Pydantic models

    tests/            # unit and integration tests
```
