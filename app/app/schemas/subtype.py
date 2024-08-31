from typing import Annotated
from typing_extensions import Self

from fastapi import Query
from pydantic import BaseModel, model_validator

# Define a Pydantic model for the book
class SubtypeCreate(BaseModel):
    name: str
    parent: str | None = None
    book: str
    properties: dict[str, str | list[str]] = {} #TODO: add special validatior for book fields
    ancestry: list[str] = []
    children: list[str] = []

class SubtypeGenerate(BaseModel):
    parent: str
    book: str
    count: Annotated[int, Query(gt=0, lt=11)] = 1
    
class SubtypeUpdate(SubtypeCreate):
    pass 
