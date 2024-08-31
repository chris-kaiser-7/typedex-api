from typing import Annotated, Any
from asyncio import gather

from fastapi import APIRouter, HTTPException, Depends
from motor import core

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=list[models.Subtype])
async def get_all_subtypes(
    *,
    page: int = 0,
) -> Any:
    return await crud.subtype.get_multi(page=page)

@router.get("/{subtype_book}/{subtype_name}", response_model=models.Subtype)
async def get_subtype(
    *,
    subtype_name: str,
    subtype_book: str
):
    subtype = await crud.subtype.get_by_name_and_book(name=subtype_name, book=subtype_book)
    if subtype is None:
        raise HTTPException(status_code=404, detail="Subtype not found")
    return subtype

@router.post("/", response_model=models.Subtype)
async def create_subtype(
    *,
    obj_in: schemas.SubtypeCreate,
    current_user: Annotated[models.User, Depends(deps.get_current_active_user)],
) -> Any:
    found_book = crud.book.get_by_name(name=obj_in.book)
    existing_subtype = crud.subtype.get_by_name_and_book(name=obj_in.name, book=obj_in.book)

    found_book, existing_subtype = await gather(found_book, existing_subtype)

    if existing_subtype:
        raise HTTPException(status_code=400, detail="Subtype with this name already exists")
    if not found_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    created_assistant = await crud.subtype.create(obj_in=obj_in)
    return created_assistant

@router.post("/generate/", response_model=list[models.Subtype])
async def create_subtype(
    *,
    obj_in: schemas.SubtypeGenerate,
    current_user: Annotated[models.User, Depends(deps.get_current_active_user)],
    db: Annotated[core.AgnosticDatabase, Depends(deps.get_db)]
) -> Any:
    existing_subtype = await crud.subtype.get_by_name_and_book(name=obj_in.parent, book=obj_in.book)
    if not existing_subtype:
        raise HTTPException(status_code=404, detail="Parent not found.")
    return await crud.subtype.generate_children(db=db, obj_in=obj_in)
