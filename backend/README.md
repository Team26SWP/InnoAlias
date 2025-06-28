# InnoAlias Backend

This folder contains a FastAPI backend for an Alias game.


## Usage
1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Copy `backend/sample.env` to `.env`:
   ```bash
   cp backend/sample.env .env
   ```
3. Run the server from the repository root:
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```


## Structure

```
backend/
    requirements.txt  # project dependencies
    sample.env        # env file for auth
    app/
        main.py       # FastAPI application
        db.py         # database connection
        code_gen.py   # code generator for the game
        services/     # services for API
        routers/      # API and websocket routers
        models/       # Pydantic models
```
