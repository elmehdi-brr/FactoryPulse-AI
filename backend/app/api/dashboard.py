from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardKPIResponse,
    DashboardOverviewResponse,
    DashboardPeriodResponse,
    DashboardProductionLineSummaryResponse,
)
from app.services.dashboard_service import (
    DashboardServiceError,
    calculate_dashboard_overview,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
)
async def get_dashboard_overview_endpoint(
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> DashboardOverviewResponse:
    try:
        metrics = await calculate_dashboard_overview(
            db,
            start_at=start_at,
            end_at=end_at,
        )
    except DashboardServiceError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc

    return DashboardOverviewResponse(
        period=DashboardPeriodResponse(
            start_at=metrics.start_at,
            end_at=metrics.end_at,
        ),
        kpis=DashboardKPIResponse(
            overall_oee=metrics.overall_oee,
            availability=metrics.availability,
            active_alert_count=(
                metrics.active_alert_count
            ),
            fleet_mtbf_seconds=(
                metrics.fleet_mtbf_seconds
            ),
        ),
        production_lines=[
            DashboardProductionLineSummaryResponse(
                id=line.id,
                name=line.name,
                code=line.code,
                oee=line.oee,
                availability=line.availability,
            )
            for line in metrics.production_lines
        ],
    )