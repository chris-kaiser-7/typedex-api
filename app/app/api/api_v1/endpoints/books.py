from fastapi import APIRouter, HTTPException, Depends
from string import Template
from asyncio import gather
from app.api import deps
from app.schemas import BookCreate
from app.models import Book, User
from app import crud
from typing import Annotated, Any
import logging

def create_string_from_template(template_string, values):
    template = Template(template_string)
    return template.substitute(values)

# Create an APIRouter instance
router = APIRouter(
    prefix="/books",
    tags=["books"]
)

@router.get("/", response_model=list[Book])
async def read_book(
    page: int = 0
) -> list[Book]:
    return await crud.book.get_multi(page=page)

@router.get("/{book_name}")
async def read_book(
    book_name: str
) -> Book:
    found_book = await crud.book.get_by_name(name=book_name)
    if not found_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return found_book

@router.post("/",response_model=Book)
async def create_book(
    book: BookCreate,
    current_user: Annotated[User, Depends(deps.get_current_active_user)],
) -> Any:
    found_book = crud.book.get_by_name(name=book.name)
    assistant = crud.assistant.get_by_name(name=book.assistant)

    found_book, assistant = await gather(found_book, assistant)

    if found_book:
        raise HTTPException(status_code=400, detail="Book already exists")
    if not assistant:
        raise HTTPException(status_code=400, detail="Assistant does not exist")

    created_book = await crud.book.create_from_template(obj_in=book, template=assistant.template)
    if not created_book:
        raise HTTPException(status_code=400, detail="Error creating book.")

    return created_book

# # Delete a book by name
# @router.delete("/books/{book_name}")
# async def delete_book(book_name: str):
#     result = await router.book_collection.delete_one({"name": book_name})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Book not found")
#     return {"message": "Book deleted successfully"}