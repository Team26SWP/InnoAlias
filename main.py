from models import *

from fastapi import FastAPI, WebSocket, HTTPException
from pymongo import MongoClient
from random import shuffle
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017')
db = client.db
games = db.games

app = FastAPI()

connections: dict[str, WebSocket] = {}


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, game_id: str) -> bool:
        await websocket.accept()

        if game_id in self.connections:
            await websocket.close(code=1008, reason="Game already active and host is connected")
            return False

        self.connections[game_id] = websocket
        print(f"Connected to ${game_id}")

        return True

    def disconnect(self, game_id: str):
        if game_id in self.connections:
            del self.connections[game_id]
            print(f"Disconnected from ${game_id}")

    async def send_state(self, game_id: str, state: dict):
        if game_id in self.connections:
            websocket = self.connections[game_id]
            await websocket.send_json(state)


manager = ConnectionManager()


@app.post("/create/game")
def create_game(game: Game):
    words = game.remaining_words
    shuffle(words)

    result = games.insert_one(game.model_dump(by_alias=True))
    return {"id": str(result.inserted_id)}


@app.websocket("/game/{game_id}")
async def handle_game(websocket: WebSocket, game_id: str):
    connected = manager.connect(websocket, game_id)
    if not connected:
        raise HTTPException(status_code=404)
    try:
        while True:
            #json с game_id
            data = await websocket.receive_json()
            action = data["action"]
            doc = games.find_one({"game_id": game_id})

            if doc is None:
                manager.disconnect(game_id)
                raise HTTPException(status_code=404, detail="Game not found")

            if action == "skip":
                word_list = doc.get("remaining_words")
                new_word = word_list.pop()
                games.update_one({"_id": "game_id"}, {"$set":
                                                          {"remaining_words": word_list, "current_word": new_word}})
                await manager.send_state(game_id, {
                    "expires_at": datetime.now() + timedelta(seconds=60),
                    "remaining_words": word_list,
                    "current_word": new_word,
                })
    except:
        manager.disconnect(game_id)
        raise HTTPException(status_code=404)
