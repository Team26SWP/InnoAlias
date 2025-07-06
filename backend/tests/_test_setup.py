import os
import types
import sys
import mongomock_motor

motor_mock = types.ModuleType("motor")
motor_asyncio = types.ModuleType("motor.motor_asyncio")
setattr(motor_asyncio, "AsyncIOMotorClient", mongomock_motor.AsyncMongoMockClient)
setattr(motor_mock, "motor_asyncio", motor_asyncio)
sys.modules.setdefault("motor", motor_mock)
sys.modules.setdefault("motor.motor_asyncio", motor_asyncio)

os.environ.setdefault("SECRET_KEY", "test_secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("GEMINI_API_KEY", "test_api_key")
os.environ.setdefault("GEMINI_MODEL_NAME", "test_model_name")
