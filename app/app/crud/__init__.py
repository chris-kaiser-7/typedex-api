from .crud_user import user
from .crud_token import token
from .crud_book import book
from .crud_assistant import assistant
from .crud_subtype import subtype


# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
