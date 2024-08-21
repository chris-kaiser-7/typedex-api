from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from ..db_models import Assistant
from ..main import app

router = APIRouter()

# Placeholder for your MongoDB client
db = AsyncIOMotorClient().your_database_name  # Replace 'your_database_name' with your actual database name

# Endpoint to retrieve all Assistants
@router.get("/assistants/", response_model=List[Assistant])
async def get_all_assistants():
    return await app.assistant_collection.find().to_list(length=500)

# Endpoint to retrieve a specific Assistant by ID
@router.get("/assistants/{assistant_id}", response_model=Assistant)
async def get_assistant(assistant_name: str):
    assistant = await app.assistant_collection.find_one({"name": assistant_name})
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant

# Endpoint to add a new Assistant
@router.post("/assistants/", response_model=Assistant)
async def create_assistant(assistant: Assistant):
    existing_assistant = await app.assistant_collection.find_one({"name": assistant.name})
    if existing_assistant:
        raise HTTPException(status_code=400, detail="Assistant with this name already exists")
    await app.assistant_collection.insert_one(assistant.model_dump())
    return assistant