from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.processing import AIProcessingStatus
from app.models.ai_processing_state import AIProcessingState


async def get_ai_processing_state_by_id(
    db: AsyncSession,
    state_id: int,
) -> AIProcessingState | None:
    result = await db.execute(
        select(AIProcessingState)
        .where(
            AIProcessingState.id == state_id
        )
        .execution_options(
            populate_existing=True
        )
    )

    return result.scalar_one_or_none()


async def get_ai_processing_state(
    db: AsyncSession,
    source_reading_id: int,
    model_name: str,
    model_version: str | None,
) -> AIProcessingState | None:
    query = (
        select(AIProcessingState)
        .where(
            AIProcessingState.source_reading_id
            == source_reading_id,
            AIProcessingState.model_name == model_name,
        )
        .execution_options(
            populate_existing=True
        )
    )

    if model_version is None:
        query = query.where(
            AIProcessingState.model_version.is_(None)
        )
    else:
        query = query.where(
            AIProcessingState.model_version
            == model_version
        )

    result = await db.execute(query)

    return result.scalar_one_or_none()


async def start_ai_processing_attempt(
    db: AsyncSession,
    source_reading_id: int,
    model_name: str,
    model_version: str | None,
) -> AIProcessingState:
    statement = (
        insert(AIProcessingState)
        .values(
            source_reading_id=source_reading_id,
            model_name=model_name,
            model_version=model_version,
            status=AIProcessingStatus.PROCESSING.value,
            attempt_count=1,
        )
        .on_conflict_do_update(
            index_elements=[
                AIProcessingState.source_reading_id,
                AIProcessingState.model_name,
                AIProcessingState.model_version,
            ],
            set_={
                "status": AIProcessingStatus.PROCESSING.value,
                "attempt_count": (
                    AIProcessingState.attempt_count + 1
                ),
                "last_attempt_at": func.now(),
                "completed_at": None,
                "last_error": None,
            },
        )
        .returning(AIProcessingState.id)
    )

    result = await db.execute(statement)

    state_id = result.scalar_one()

    await db.commit()

    state = await get_ai_processing_state_by_id(
        db,
        state_id,
    )

    if state is None:
        raise RuntimeError(
            "AI processing state could not be loaded"
        )

    return state


async def complete_ai_processing_attempt(
    db: AsyncSession,
    state_id: int,
    status: AIProcessingStatus,
    last_error: str | None = None,
) -> AIProcessingState:
    if status == AIProcessingStatus.PROCESSING:
        raise ValueError(
            "Processing is not a terminal AI processing status"
        )

    statement = (
        update(AIProcessingState)
        .where(
            AIProcessingState.id == state_id
        )
        .values(
            status=status.value,
            completed_at=func.now(),
            last_error=last_error,
        )
        .returning(AIProcessingState.id)
    )

    result = await db.execute(statement)

    updated_state_id = result.scalar_one_or_none()

    if updated_state_id is None:
        await db.rollback()

        raise ValueError(
            "AI processing state not found"
        )

    await db.commit()

    state = await get_ai_processing_state_by_id(
        db,
        updated_state_id,
    )

    if state is None:
        raise RuntimeError(
            "AI processing state could not be loaded"
        )

    return state

async def get_ai_processing_states_by_reading(
    db: AsyncSession,
    source_reading_id: int,
) -> list[AIProcessingState]:
    result = await db.execute(
        select(AIProcessingState)
        .where(
            AIProcessingState.source_reading_id
            == source_reading_id
        )
        .order_by(
            AIProcessingState.id
        )
    )

    return list(result.scalars().all())