from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.machines import router as machines_router
from app.api.sensors import router as sensors_router
from app.api.sensor_readings import router as sensor_readings_router
from app.api.predictions import router as predictions_router
from app.api.alerts import router as alerts_router
from app.api.notifications import router as notifications_router
from app.api.maintenance_records import router as maintenance_records_router
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.roles import router as roles_router
from app.api.users import router as users_router


app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(machines_router)
app.include_router(sensors_router)
app.include_router(sensor_readings_router)
app.include_router(predictions_router)
app.include_router(alerts_router)
app.include_router(notifications_router)
app.include_router(maintenance_records_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)