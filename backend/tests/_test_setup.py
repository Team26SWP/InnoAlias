import os
import sys
import types

import mongomock_motor

motor_mock = types.ModuleType("motor")
motor_asyncio = types.ModuleType("motor.motor_asyncio")
motor_asyncio.AsyncIOMotorClient = mongomock_motor.AsyncMongoMockClient  # type: ignore[attr-defined]
motor_mock.motor_asyncio = motor_asyncio  # type: ignore[attr-defined]
sys.modules.setdefault("motor", motor_mock)
sys.modules.setdefault("motor.motor_asyncio", motor_asyncio)

os.environ.setdefault("SECRET_KEY", "test_secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("GEMINI_API_KEY", "test_api_key")
os.environ.setdefault("GEMINI_MODEL_NAME", "test_model_name")
