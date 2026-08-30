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
    DashboardMachineHealthResponse,
    DashboardNeedsAttentionResponse,
    DashboardOverviewResponse,
    DashboardPeriodResponse,
    DashboardProductionLineSummaryResponse,
    DashboardRecentAlertResponse,
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

    needs_attention = metrics.needs_attention

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
        machine_health=DashboardMachineHealthResponse(
            total_machines=(
                metrics.machine_health.total_machines
            ),
            healthy_count=(
                metrics.machine_health.healthy_count
            ),
            attention_count=(
                metrics.machine_health.attention_count
            ),
            critical_count=(
                metrics.machine_health.critical_count
            ),
        ),
        recent_alerts=[
            DashboardRecentAlertResponse(
                id=alert.id,
                machine_id=alert.machine_id,
                machine_name=alert.machine_name,
                machine_code=alert.machine_code,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                created_at=alert.created_at,
            )
            for alert in metrics.recent_alerts
        ],
        needs_attention=(
            DashboardNeedsAttentionResponse(
                machine_id=(
                    needs_attention.machine_id
                ),
                machine_name=(
                    needs_attention.machine_name
                ),
                machine_code=(
                    needs_attention.machine_code
                ),
                production_line_id=(
                    needs_attention.production_line_id
                ),
                production_line_name=(
                    needs_attention.production_line_name
                ),
                priority_rank=(
                    needs_attention.priority_rank
                ),
                recorded_downtime_seconds=(
                    needs_attention
                    .recorded_downtime_seconds
                ),
                failure_count=(
                    needs_attention.failure_count
                ),
                mttr_seconds=(
                    needs_attention.mttr_seconds
                ),
                mtbf_seconds=(
                    needs_attention.mtbf_seconds
                ),
                dominant_reason=(
                    needs_attention.dominant_reason
                ),
                dominant_reason_percentage=(
                    needs_attention
                    .dominant_reason_percentage
                ),
            )
            if needs_attention is not None
            else None
        ),
    )