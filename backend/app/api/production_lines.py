from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.production_line import (
    ProductionLineCreate,
    ProductionLineResponse,
    ProductionLineUpdate,
)
from app.schemas.production_analytics import (
    ProductionLineOEEResponse,
)
from app.schemas.operational_intelligence import (
    MachineDowntimeReasonBreakdownResponse,
    MachineDowntimeReasonSummaryResponse,
    OperationalDowntimeSummaryResponse,
    OperationalMachineImpactResponse,
    OperationalMachinePriorityResponse,
    OperationalOEEResponse,
    OperationalPrioritySummaryResponse,
    ProductionLineOperationalIntelligenceResponse,
)
from app.schemas.operational_trends import (
    MachineOperationalTrendResponse,
    OperationalMetricTrendResponse,
    OperationalTrendPeriodResponse,
    OperationalTrendSummaryResponse,
    ProductionLineOperationalTrendsResponse,
)
from app.schemas.machine import MachineResponse
from app.services.area_service import get_area_by_id
from app.services.production_line_service import (
    create_production_line,
    get_production_line_by_code,
    get_production_line_by_id,
    get_production_lines,
    update_production_line,
)
from app.services.machine_service import get_machines_by_production_line
from app.services.production_analytics_service import (
    ProductionAnalyticsServiceError,
    calculate_production_line_oee,
)
from app.schemas.downtime_analytics import (
    ProductionLineDowntimeAnalyticsResponse,
)
from app.services.downtime_analytics_service import (
    DowntimeAnalyticsServiceError,
    calculate_production_line_downtime_analytics,
)
from app.services.operational_intelligence_service import (
    OperationalIntelligenceServiceError,
    calculate_production_line_operational_intelligence,
)
from app.services.operational_trends_service import (
    OperationalTrendsServiceError,
    calculate_production_line_operational_trends,
)


router = APIRouter(
    prefix="/production-lines",
    tags=["Production Lines"],
)


@router.post(
    "",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_production_line_endpoint(
    line_data: ProductionLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> ProductionLineResponse:
    area = await get_area_by_id(
        db,
        line_data.area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    existing_line = await get_production_line_by_code(
        db,
        line_data.code,
    )

    if existing_line is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Production line code already exists",
        )

    return await create_production_line(
        db,
        line_data,
    )


@router.get(
    "",
    response_model=list[ProductionLineResponse],
)
async def get_production_lines_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[ProductionLineResponse]:
    return await get_production_lines(db)


@router.get(
    "/{production_line_id}",
    response_model=ProductionLineResponse,
)
async def get_production_line_endpoint(
    production_line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ProductionLineResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    return production_line

@router.get(
    "/{production_line_id}/oee",
    response_model=ProductionLineOEEResponse,
)
async def get_production_line_oee_endpoint(
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> ProductionLineOEEResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    try:
        metrics = await calculate_production_line_oee(
            db,
            production_line_id,
            start_at=start_at,
            end_at=end_at,
        )
    except ProductionAnalyticsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ProductionLineOEEResponse(
        production_line_id=production_line_id,
        start_at=start_at,
        end_at=end_at,
        run_count=metrics.run_count,
        scheduled_time_seconds=(
            metrics.scheduled_time_seconds
        ),
        planned_downtime_seconds=(
            metrics.planned_downtime_seconds
        ),
        planned_production_time_seconds=(
            metrics.planned_production_time_seconds
        ),
        unplanned_downtime_seconds=(
            metrics.unplanned_downtime_seconds
        ),
        operating_time_seconds=(
            metrics.operating_time_seconds
        ),
        total_quantity=metrics.total_quantity,
        good_quantity=metrics.good_quantity,
        availability=metrics.availability,
        performance=metrics.performance,
        quality=metrics.quality,
        oee=metrics.oee,
    )


@router.patch(
    "/{production_line_id}",
    response_model=ProductionLineResponse,
)
async def update_production_line_endpoint(
    production_line_id: int,
    line_data: ProductionLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> ProductionLineResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    if line_data.area_id is not None:
        area = await get_area_by_id(
            db,
            line_data.area_id,
        )

        if area is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Area not found",
            )

    if line_data.code is not None:
        existing_line = await get_production_line_by_code(
            db,
            line_data.code,
        )

        if (
            existing_line is not None
            and existing_line.id != production_line_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Production line code already exists",
            )

    return await update_production_line(
        db,
        production_line,
        line_data,
    )


@router.get(
    "/{production_line_id}/downtime-analytics",
    response_model=ProductionLineDowntimeAnalyticsResponse,
)
async def get_production_line_downtime_analytics_endpoint(
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> ProductionLineDowntimeAnalyticsResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    try:
        result = (
            await calculate_production_line_downtime_analytics(
                db,
                production_line_id,
                start_at=start_at,
                end_at=end_at,
            )
        )
    except DowntimeAnalyticsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    metrics = result.metrics

    return ProductionLineDowntimeAnalyticsResponse(
        production_line_id=production_line_id,
        start_at=start_at,
        end_at=end_at,
        run_count=result.run_count,
        event_count=metrics.event_count,
        recorded_downtime_seconds=(
            metrics.recorded_downtime_seconds
        ),
        planned_downtime_seconds=(
            metrics.planned_downtime_seconds
        ),
        unplanned_downtime_seconds=(
            metrics.unplanned_downtime_seconds
        ),
        by_reason=[
            {
                "reason": item.reason,
                "event_count": item.event_count,
                "duration_seconds": item.duration_seconds,
                "percentage": item.percentage,
            }
            for item in metrics.by_reason
        ],
        by_machine=[
            {
                "machine_id": item.machine_id,
                "event_count": item.event_count,
                "duration_seconds": item.duration_seconds,
                "percentage": item.percentage,
            }
            for item in metrics.by_machine
        ],
    )

@router.get(
    "/{production_line_id}/operational-intelligence",
    response_model=ProductionLineOperationalIntelligenceResponse,
)
async def get_production_line_operational_intelligence_endpoint(
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> ProductionLineOperationalIntelligenceResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    try:
        result = (
            await calculate_production_line_operational_intelligence(
                db,
                production_line_id,
                start_at=start_at,
                end_at=end_at,
            )
        )
    except OperationalIntelligenceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    oee = result.oee
    impact = result.operational_impact
    priority = result.priority
    downtime_reasons = result.downtime_reasons

    return ProductionLineOperationalIntelligenceResponse(
        production_line_id=production_line_id,
        start_at=start_at,
        end_at=end_at,
        run_count=result.run_count,

        oee=OperationalOEEResponse(
            run_count=oee.run_count,
            scheduled_time_seconds=(
                oee.scheduled_time_seconds
            ),
            planned_downtime_seconds=(
                oee.planned_downtime_seconds
            ),
            planned_production_time_seconds=(
                oee.planned_production_time_seconds
            ),
            unplanned_downtime_seconds=(
                oee.unplanned_downtime_seconds
            ),
            operating_time_seconds=(
                oee.operating_time_seconds
            ),
            total_quantity=oee.total_quantity,
            good_quantity=oee.good_quantity,
            availability=oee.availability,
            performance=oee.performance,
            quality=oee.quality,
            oee=oee.oee,
        ),

        operational_impact=(
            OperationalDowntimeSummaryResponse(
                recorded_downtime_seconds=(
                    impact.recorded_downtime_seconds
                ),
                machine_attributed_recorded_downtime_seconds=(
                    impact
                    .machine_attributed_recorded_downtime_seconds
                ),
                unattributed_recorded_downtime_seconds=(
                    impact
                    .unattributed_recorded_downtime_seconds
                ),
                machine_attributed_share=(
                    impact.machine_attributed_share
                ),
                unattributed_share=(
                    impact.unattributed_share
                ),
                top_downtime_machine_id=(
                    impact.top_downtime_machine_id
                ),
                machines=[
                    OperationalMachineImpactResponse(
                        machine_id=machine.machine_id,
                        machine_name=machine.machine_name,
                        machine_code=machine.machine_code,
                        recorded_downtime_event_count=(
                            machine
                            .recorded_downtime_event_count
                        ),
                        recorded_downtime_seconds=(
                            machine.recorded_downtime_seconds
                        ),
                        recorded_downtime_share=(
                            machine.recorded_downtime_share
                        ),
                        failure_count=(
                            machine.failure_count
                        ),
                        mttr_seconds=(
                            machine.mttr_seconds
                        ),
                        operating_exposure_seconds=(
                            machine
                            .operating_exposure_seconds
                        ),
                        mtbf_seconds=(
                            machine.mtbf_seconds
                        ),
                    )
                    for machine in impact.machines
                ],
            )
        ),
        priority=OperationalPrioritySummaryResponse(
            top_priority_machine_id=(
                priority.top_priority_machine_id
            ),
            machines=[
                OperationalMachinePriorityResponse(
                    machine_id=machine.machine_id,
                    machine_name=machine.machine_name,
                    machine_code=machine.machine_code,
                    priority_rank=machine.priority_rank,
                    downtime_rank=machine.downtime_rank,
                    failure_rank=machine.failure_rank,
                    mttr_rank=machine.mttr_rank,
                    mtbf_rank=machine.mtbf_rank,
                )
                for machine in priority.machines
            ],
        ),
        downtime_reasons=[
            MachineDowntimeReasonSummaryResponse(
                machine_id=machine.machine_id,
                event_count=machine.event_count,
                recorded_downtime_seconds=(
                    machine.recorded_downtime_seconds
                ),
                dominant_duration_reason=(
                    machine.dominant_duration_reason
                ),
                most_frequent_reason=(
                    machine.most_frequent_reason
                ),
                by_reason=[
                    MachineDowntimeReasonBreakdownResponse(
                        reason=reason.reason,
                        event_count=reason.event_count,
                        duration_seconds=(
                            reason.duration_seconds
                        ),
                        percentage=reason.percentage,
                        planned_event_count=(
                            reason.planned_event_count
                        ),
                        planned_duration_seconds=(
                            reason.planned_duration_seconds
                        ),
                        unplanned_event_count=(
                            reason.unplanned_event_count
                        ),
                        unplanned_duration_seconds=(
                            reason.unplanned_duration_seconds
                        ),
                    )
                    for reason in machine.by_reason
                ],
            )
            for machine in downtime_reasons
        ],
    )


@router.get(
    "/{production_line_id}/operational-trends",
    response_model=ProductionLineOperationalTrendsResponse,
)
async def get_production_line_operational_trends_endpoint(
    production_line_id: int,
    start_at: datetime,
    end_at: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> ProductionLineOperationalTrendsResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    try:
        result = (
            await calculate_production_line_operational_trends(
                db,
                production_line_id,
                start_at=start_at,
                end_at=end_at,
            )
        )
    except OperationalTrendsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    trends = result.trends

    def metric_response(
        metric,
    ) -> OperationalMetricTrendResponse:
        return OperationalMetricTrendResponse(
            current_value=metric.current_value,
            previous_value=metric.previous_value,
            delta=metric.delta,
            direction=metric.direction,
        )

    return ProductionLineOperationalTrendsResponse(
        production_line_id=production_line_id,

        current_period=OperationalTrendPeriodResponse(
            start_at=result.current_period.start_at,
            end_at=result.current_period.end_at,
        ),

        previous_period=OperationalTrendPeriodResponse(
            start_at=result.previous_period.start_at,
            end_at=result.previous_period.end_at,
        ),

        trends=OperationalTrendSummaryResponse(
            oee=metric_response(
                trends.oee
            ),
            availability=metric_response(
                trends.availability
            ),
            performance=metric_response(
                trends.performance
            ),
            quality=metric_response(
                trends.quality
            ),
            recorded_downtime=metric_response(
                trends.recorded_downtime
            ),
            total_failure_count=metric_response(
                trends.total_failure_count
            ),

            machines=[
                MachineOperationalTrendResponse(
                    machine_id=machine.machine_id,
                    machine_name=machine.machine_name,
                    machine_code=machine.machine_code,

                    recorded_downtime=metric_response(
                        machine.recorded_downtime
                    ),
                    failure_count=metric_response(
                        machine.failure_count
                    ),
                    mttr=metric_response(
                        machine.mttr
                    ),
                    mtbf=metric_response(
                        machine.mtbf
                    ),
                )
                for machine in trends.machines
            ],
        ),
    )


@router.get(
    "/{production_line_id}/machines",
    response_model=list[MachineResponse],
)
async def get_production_line_machines_endpoint(
    production_line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[MachineResponse]:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    return await get_machines_by_production_line(
        db,
        production_line_id,
    ) 