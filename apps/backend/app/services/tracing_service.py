import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trace import TraceRecord

logger = logging.getLogger(__name__)


class TracingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_trace(
        self,
        trace_id: str,
        project_id: str,
        query: str,
        answer: Optional[str],
        total_latency_ms: float,
        configuration: Dict[str, Any],
        spans: List[Dict[str, Any]],
        input_tokens: int = 0,
        output_tokens: int = 0,
        user_id: Optional[str] = None,
        status: str = "SUCCESS"
    ) -> TraceRecord:
        record = TraceRecord(
            id=trace_id,
            project_id=project_id,
            user_id=user_id,
            query=query,
            answer=answer,
            status=status,
            total_latency_ms=total_latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            configuration_json=configuration,
            spans_json=spans
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_traces(
        self,
        project_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[TraceRecord]:
        stmt = (
            select(TraceRecord)
            .where(TraceRecord.project_id == project_id)
            .order_by(desc(TraceRecord.created_at))
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        stmt = select(TraceRecord).where(TraceRecord.id == trace_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
