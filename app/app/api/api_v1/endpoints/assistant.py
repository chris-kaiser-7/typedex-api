from typing import Annotated, Any, List

from fastapi import APIRouter, HTTPException, Depends

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

# Endpoint to retrieve all Assistants
@router.get("/", response_model=List[models.Assistant])
async def get_all_assistants(
    *,
    page: int = 0,
):
    return await crud.assistant.get_multi(page=page)

# Endpoint to retrieve a specific Assistant by ID
@router.get("/{assistant_id}", response_model=models.Assistant)
async def get_assistant(
    *,
    assistant_name: str,
    current_user: Annotated[models.User, Depends(deps.get_current_active_user)],
):
    assistant = await crud.assistant.get_by_name(name=assistant_name)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant

# Endpoint to add a new Assistant
@router.post("/", response_model=models.Assistant)
async def create_assistant(
    *,
    obj_in: schemas.AssistantCreate,
    current_user: Annotated[models.User, Depends(deps.get_current_active_user)],
) -> Any:
    existing_assistant = await crud.assistant.get_by_name(name=obj_in.name)
    if existing_assistant:
        raise HTTPException(status_code=400, detail="Assistant with this name already exists")
    created_assistant = await crud.assistant.create(obj_in=obj_in)
    return created_assistant