import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
import json
from app.whatsapp.logger import logger
from app.models.conversation_session import ConversationSession
from app.schemas.conversation_session import ConversationSessionCreate, ConversationSessionUpdate
from app.services.base import CRUDBase

class CRUDConversationSession(CRUDBase[ConversationSession, ConversationSessionCreate, ConversationSessionUpdate]):
    
    async def get_active_session(self, db: AsyncSession, phone_number: str) -> Optional[ConversationSession]:
        result = await db.execute(select(self.model).where(self.model.phone_number == phone_number))
        return result.scalars().first()

    async def start_session(self, db: AsyncSession, phone_number: str, flow: str, step: str) -> ConversationSession:
        # PostgreSQL UPSERT logic to ensure only one session per phone number
        stmt = insert(self.model).values(
            phone_number=phone_number,
            current_flow=flow,
            current_step=step,
            collected_data={}
        )
        
        # On conflict (phone_number), overwrite with new flow
        stmt = stmt.on_conflict_do_update(
            index_elements=['phone_number'],
            set_={
                'current_flow': flow,
                'current_step': step,
                'collected_data': {}
            }
        ).returning(self.model)
        
        result = await db.execute(stmt)
        await db.commit()
        session_obj = result.scalars().first()
        
        logger.info(json.dumps({
            "action": "session_started",
            "phone": phone_number,
            "flow": flow,
            "step": step
        }))
        
        return session_obj

    async def update_step(self, db: AsyncSession, phone_number: str, step: str, new_data: Dict[str, Any]) -> Optional[ConversationSession]:
        session_obj = await self.get_active_session(db, phone_number)
        if not session_obj:
            return None
            
        # Update JSONB data explicitly by merging dicts
        updated_data = dict(session_obj.collected_data)
        updated_data.update(new_data)
        
        session_obj.current_step = step
        session_obj.collected_data = updated_data
        
        db.add(session_obj)
        await db.commit()
        await db.refresh(session_obj)
        return session_obj

    async def clear_session(self, db: AsyncSession, phone_number: str) -> None:
        await db.execute(delete(self.model).where(self.model.phone_number == phone_number))
        await db.commit()
        
        logger.info(json.dumps({
            "action": "session_cleared",
            "phone": phone_number
        }))

conversation_service = CRUDConversationSession(ConversationSession)
