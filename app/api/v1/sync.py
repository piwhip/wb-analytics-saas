from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.analytics import SyncResult
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/run", response_model=SyncResult)
async def sync_now(
    user: CurrentUser,
    db: DBSession,
    days_back: int = Query(30, ge=1, le=180),
) -> SyncResult:
    """Синхронная выгрузка данных WB (удобно для демо и отладки).

    Для регулярной фоновой синхронизации см. POST /sync/schedule.
    """
    if not user.wb_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connect your WB token first (PUT /users/me/wb-token)",
        )
    result = await SyncService(db).sync_user(user, days_back=days_back)
    return SyncResult(**result)


@router.post("/schedule", status_code=status.HTTP_202_ACCEPTED)
async def schedule_sync(user: CurrentUser, days_back: int = Query(30, ge=1, le=180)):
    """Поставить синхронизацию в очередь Celery (фоновая обработка)."""
    if not user.wb_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connect your WB token first (PUT /users/me/wb-token)",
        )

    from app.workers.tasks import sync_user_task

    task = sync_user_task.delay(user.id, days_back)
    return {"task_id": task.id, "status": "queued"}
