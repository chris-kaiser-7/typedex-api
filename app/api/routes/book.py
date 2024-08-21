from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from typing_extensions import Self
from typing import List
from bson import ObjectId
from string import Template
from ..db_models import Book
from asyncio import gather

def create_string_from_template(template_string, values):
    template = Template(template_string)
    return template.substitute(values)

# Define a Pydantic model for the book
class BookRequest(BaseModel):
    name: str
    fields: List[str] #need to add validation that can't have spaces
    field_descriptions: List[str]
    assistant: str

    @model_validator(mode='after')
    def validate_fields_and_descriptions(self) -> Self:
        if len(self.fields) != len(self.field_descriptions):
            raise ValueError("fields and field_descriptions must have the same length")
        return self

# Create an APIRouter instance
router = APIRouter(
    prefix="/books",
    tags=["books"]
)

# Read a book by name
@router.get("/books/{book_name}")
async def read_book(book_name: str) -> Book:
    book_raw = await router.book_collection.find_one({"name": book_name})
    if not book_raw:
        raise HTTPException(status_code=404, detail="Book not found")
    book = Book(**book_raw)
    
    return book

# Create a new book
@router.post("/books")
async def create_book(book: BookRequest) -> Book:
    found_book = router.book_collection.find_one({"name": book.name})
    assistant = router.assistant_collection.find_one({"name": book.assistant})
    # await found_book
    # await assistant
    await gather(found_book, assistant)

    if found_book:
        raise HTTPException(status_code=400, detail="Book already exists")
    if not assistant:
        raise HTTPException(status_code=400, detail="Assistant does not exist")

    fields_obj = {'fields': book.fields, 'field_descriptions': book.field_descriptions}
    instructions = create_string_from_template(assistant["template"], fields_obj) + '\n'
    instructions += f'```json\n[{{"name":"the name",'
    for field, descriptions in zip(book.fields, book.field_descriptions):
        instructions += f'"{field}": "{descriptions}",'
    instructions = instructions[:-1]
    instructions += '}]\n```'

    # Insert the book into the collection
    book_dict = book.model_dump()
    book_dict["instructions"] = instructions
    router.book_collection.insert_one(book_dict)
    return {"message": "Book created successfully", "book": book_dict}

# Delete a book by name
@router.delete("/books/{book_name}")
async def delete_book(book_name: str):
    result = await router.book_collection.delete_one({"name": book_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}
