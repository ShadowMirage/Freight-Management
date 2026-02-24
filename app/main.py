from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import users, trucks, loads, bookings, payments
from app.whatsapp.webhook import router as whatsapp_router

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# Include Routers
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(trucks.router, prefix=f"{settings.API_V1_STR}/trucks", tags=["trucks"])
app.include_router(loads.router, prefix=f"{settings.API_V1_STR}/loads", tags=["loads"])
app.include_router(bookings.router, prefix=f"{settings.API_V1_STR}/bookings", tags=["bookings"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])

# WhatsApp Webhook Router
app.include_router(whatsapp_router, prefix=f"{settings.API_V1_STR}/whatsapp", tags=["whatsapp"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/full")
async def health_check_full():
    from app.system.diagnostics import run_startup_diagnostics
    report = await run_startup_diagnostics()
    return {
        "status": "healthy" if not any(v.get("level") == "CRITICAL" and v.get("status") != "OK" for v in report.values()) else "unhealthy",
        "diagnostics": report
    }

@app.on_event("startup")
async def startup_event():
    import asyncio
    from app.workers.expiry_worker import start_reservation_expiry_worker
    from app.system.diagnostics import run_startup_diagnostics, format_diagnostic_report
    
    # 1. Start Workers
    asyncio.create_task(start_reservation_expiry_worker())
    
    # 2. Run Diagnostics
    report = await run_startup_diagnostics()
    banner, critical_failure = format_diagnostic_report(report)
    
    print("\n" + banner + "\n")
    
    if critical_failure:
        raise RuntimeError("Critical system failure during startup. Abandoning boot sequence.")
