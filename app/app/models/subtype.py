from typing import Any, Optional 
from app.db.base_class import Base
from odmantic import Field

class Subtype(Base):
    name: str = Field() #TODO: need validation to be unique with book. Can make a book+name hash and make it unique.
    # parent: str | None = Field(default=None)
    parent: Optional[str] = Field(default=None)
    book: str = Field() #TODO: Add validation that book exisists in book collection. 
    properties: dict[str, Any] = Field()
    ancestry: list[str]
    children: list[str]