from app.db.base_class import Base
from odmantic import Field

class Assistant(Base):
    name: str = Field(default="", unique=True)
    template: str = Field(default="")