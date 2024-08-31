from app.crud.base import CRUDBase
from app.models import Assistant
from app.schemas import AssistantCreate, AssistantUpdate


class CRUDAssistant(CRUDBase[Assistant, AssistantCreate, AssistantUpdate]):
    async def get_by_name(self, *, name: str) -> Assistant | None:
        return await self.engine.find_one(Assistant, Assistant.name == name)

assistant = CRUDAssistant(Assistant)